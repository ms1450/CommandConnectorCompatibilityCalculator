"""
Author: Mehul Sen
Co-Author: Ian Young

Purpose: Import a list of third-party cameras and return to the terminal
    which cameras are compatible with the cloud connector.
"""

import re
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple, Union

import colorama
import pandas as pd
from colorama import Fore, Style
from tabulate import tabulate
from thefuzz import fuzz, process

# Initialize colorized output
colorama.init(autoreset=True)


@dataclass
class CompatibleModel:
    """Represents a compatible model with its details.

    Args:
        model_name (str): The name of the model.
        manufacturer (str): The manufacturer of the model.
        minimum_supported_firmware_version (str): The minimum firmware
            version that the model supports.
        notes (str): Additional notes regarding the model.

    Attributes:
        channels (int): The number of channels associated with the model,
            initialized to 0.
    """

    model_name: str
    manufacturer: str
    minimum_supported_firmware_version: str
    notes: str
    channels: int = 0


def get_camera_list(
    compatible_models: Union[List[CompatibleModel], Dict[str, CompatibleModel]]
) -> List[str]:
    """Retrieve a list of camera names from compatible models.

    Args:
        compatible_models
        (Union[List[CompatibleModel], Dict[str, CompatibleModel]]): A
            list of model objects or a dictionary of models.

    Returns:
        List[str]: A list of camera names or model keys, or an empty list
            if the input is invalid.
    """
    if isinstance(compatible_models, list):
        return [model.model_name for model in compatible_models]

    if isinstance(compatible_models, dict):
        return list(compatible_models.keys())

    return []


def get_manufacturer_list(
    compatible_models: Union[List[CompatibleModel]],
) -> set[str]:
    """Retrieve a set of camera manufacturer names from compatible models.

    Args:
        compatible_models
        (Union[List[CompatibleModel]]): A list of model objects.

    Returns:
        set[str]: A set of camera manufacturer names or an empty set
            if the input is invalid.
    """
    if isinstance(compatible_models, list):
        return {model.manufacturer.lower() for model in compatible_models}
    manufacturers: set[str] = set()
    return manufacturers


def find_matching_camera(
    camera_name: str, verkada_cameras: List[CompatibleModel]
) -> Optional[CompatibleModel]:
    """Find a matching camera by its name.

    Args:
        camera_name (str): The name of the camera to search for.
        verkada_cameras (List[CompatibleModel]): List of compatible
            models.

    Returns:
        Optional[CompatibleModel]: The matching camera object if found,
            otherwise None.
    """
    return next(
        (
            camera
            for camera in verkada_cameras
            if camera.model_name == camera_name.lower()
        ),
        None,
    )


def parse_compatibility_list(filename: str) -> List[CompatibleModel]:
    """Parse a CSV file to create a list of compatible models.

    This function reads a specified CSV file, skipping the first five
    rows, and constructs a list of CompatibleModel objects from the
    remaining rows. It returns the list of compatible models for further
    processing.

    Args:
        filename (str): The path to the CSV file containing compatibility
            data.

    Returns:
        list: A list of CompatibleModel objects created from the CSV data.
    """
    compatible_models = []
    df = pd.read_csv(filename, skiprows=5, header=None, encoding="UTF-8")

    # Read the rest of the rows and create CompatibleModel objects
    for _, row in df.iterrows():
        model = CompatibleModel(row[1].lower(), row[0], row[2], row[3])
        compatible_models.append(model)
    return compatible_models


def read_customer_list(filename: str) -> pd.DataFrame:
    """Read a CSV file and transpose its rows into columns.

    This function opens a specified CSV file and reads its content,
    transposing the rows into columns for easier access. It returns a
    list of lists, where each inner list represents a column from the
    original CSV data.

    Args:
        filename (str): The path to the CSV file containing customer data.

    Returns:
        list: A list of lists, with each inner list representing a column
            from the CSV file.
    """
    return pd.read_csv(filename, dtype=str, encoding="UTF-8")


def tabulate_data(data: List[List[str]]) -> None:
    """Tabulate and print the data.

    Args:
        data (List[List[str]]): Transposed data where each list
            represents a column.
    Returns:
        None
    """
    # Extract column names (first element)
    headers = [
        f"{Fore.LIGHTBLACK_EX}{row[0]}{Style.RESET_ALL}" for row in data
    ]

    # Extract data starting from the second element
    table = [row[1:] for row in data]

    # Pair values off
    combined_data = list(zip(*table))

    # Print the tabulated data
    print(tabulate(combined_data, headers=headers, tablefmt="fancy_grid"))


def manufacturer_removed(model_name: str, manufacturers: set[str]) -> str:
    """Checks if manufacturer name is in the model name, if it is, then
    the manufacturer name gets removed.

    Args:
        model_name (str): The name of the model.
        manufacturers (set[str]): A set of manufacturer names.

    Returns:
        str: The manufacturer name removed.
    """
    if " " not in model_name:
        return model_name
    substrings = model_name.split(" ")
    filtered_substrings = [
        sub for sub in substrings if sub.lower() not in manufacturers
    ]
    return " ".join(filtered_substrings)


def identify_model_column(
    customer_cameras_raw: pd.DataFrame,
    verkada_cameras_list: List[str],
    manufacturer_list: set[str],
) -> Optional[int]:
    """Identify the column index that best matches camera models.

    Args:
        customer_cameras_raw (List[List[str]]): Raw customer camera data
            transposed into columns.
        verkada_cameras_list (List[str]): List of known Verkada camera
            model names.
        manufacturer_list (set[str]): Set of manufacturer model names.

    Returns:
        Optional[int]: The index of the column with the highest match
            score, or None if no valid scores are found.
    """

    def calculate_column_score(column_data):
        column_score = 0

        for camera in column_data.dropna():  # Remove NaN values
            if isinstance(camera, str):  # Only process strings
                camera = manufacturer_removed(
                    camera.strip(), manufacturer_list
                )
                if camera:  # Skip empty strings
                    # Perform fuzzy matching and accumulate the score
                    score = process.extractOne(
                        camera,
                        verkada_cameras_list,
                        scorer=fuzz.token_sort_ratio,
                    )[1]
                    column_score += score

        return column_score

    # Apply the score calculation to each column in the DataFrame
    scores = customer_cameras_raw.apply(calculate_column_score)

    # Get the index of the column with the highest score
    if not scores.empty and scores.max() > 0:
        return scores.idxmax()

    print(
        f"{Fore.RED}No valid scores found.{Style.RESET_ALL} Check your input data."
    )
    return None


def find_count_column(df: pd.DataFrame) -> Optional[int]:
    """Find the column index for count data using regex

    Args:
        df (Pandas.DataFrame): The DataFrame to search.

    Returns:
        Optional[int]: The index of the count column, or None if not
            present.
    """
    # Case-insensitive pattern to search
    count_column_pattern = re.compile(r"(?i)count.*|#")

    return next(
        (
            i
            for i, col in enumerate(df.columns)
            if isinstance(col, str) and count_column_pattern.match(col)
        ),
        None,
    )


def get_camera_count(
    column_number: int, customer_cameras_raw: pd.DataFrame
) -> Dict[str, int]:
    """Count the occurrences of camera names in a specified column.

    Args:
        column_number (int): The index of the column to analyze.
        customer_cameras_raw (Pandas.DataFrame): Raw customer camera data
            transposed into columns.

    Returns:
        Dict[str, int]: A dictionary containing camera names as keys and
            their occurrence counts as values.
    """
    # Check if count column exists
    count_column_index = find_count_column(customer_cameras_raw)
    camera_statistics: Dict[str, int] = {}
    if count_column_index is not None:
        count_data = customer_cameras_raw.iloc[:, count_column_index]
        camera_statistics = dict(
            zip(customer_cameras_raw.iloc[:, 0], count_data)
        )
        # Ensure the counts are integers and handle missing value cases
        return {
            str(name).strip(): 0 if pd.isna(i) or i == "nan" else int(i)
            for name, i in camera_statistics.items()
            if name
        }

    # Default to counting cameras by name
    customer_cameras_raw.T.values.tolist()
    for value in customer_cameras_raw[column_number]:
        value = value.strip()
        if value and "model" not in value.lower():
            camera_statistics[value] = camera_statistics.get(value, 0) + 1
    return camera_statistics


def strip_ansi_codes(text: str) -> str:
    """
    Removes ANSI escape codes from a given text string. This function is
    useful for cleaning up text that may contain formatting codes,
    ensuring that the output is plain and readable.

    The function uses a regular expression to identify and strip out ANSI
    codes, which are often used for terminal text formatting. The result
    is a clean string without any formatting artifacts.

    Args:
        text (str): The input string potentially containing ANSI escape
            codes.

    Returns:
        str: The cleaned string with ANSI codes removed.
    """

    return re.compile(r"\x1B[@-_][0-?]*[ -/]*[@-~]").sub("", text)


def camera_match(
    list_customer_cameras: List[str],
    verkada_cameras_list: List[str],
    verkada_cameras: List[CompatibleModel],
    manufacturer_list: set[str],
) -> List[Tuple[str, str, Optional[CompatibleModel]]]:
    """Match customer cameras against a list of known Verkada cameras.

    Args:
        list_customer_cameras (List[str]): A list of customer camera names
            to be matched.
        verkada_cameras_list (List[str]): A list of Verkada camera model
            names.
        verkada_cameras (List[CompatibleModel]): A list of CompatibleModel
            objects.
        manufacturer_list (set[str]): A set of manufacturer model

    Returns:
        List[Tuple[str, str, Optional[CompatibleModel]]]: A list of tuples
            where each tuple contains the camera name, match type, and an
            Optional CompatibleModel object.
    """

    def get_camera_obj(camera_name: str) -> Optional[CompatibleModel]:
        return find_matching_camera(camera_name, verkada_cameras)

    traced_cameras = []

    for camera in list_customer_cameras:
        if camera:
            camera_model = manufacturer_removed(camera, manufacturer_list)
            match, score = process.extractOne(
                camera_model, verkada_cameras_list, scorer=fuzz.ratio
            )
            _, sort_score = process.extractOne(
                camera_model,
                verkada_cameras_list,
                scorer=fuzz.token_sort_ratio,
            )
            _, set_score = process.extractOne(
                camera_model, verkada_cameras_list, scorer=fuzz.token_set_ratio
            )

            if score == 100 or sort_score == 100:
                traced_cameras.append(
                    (
                        camera,
                        f"{Fore.GREEN}exact{Style.RESET_ALL}",
                        get_camera_obj(match),
                    )
                )
                list_customer_cameras.remove(camera)
            elif set_score == 100:
                traced_cameras.append(
                    (
                        camera,
                        f"{Fore.CYAN}identified{Style.RESET_ALL}",
                        get_camera_obj(match),
                    )
                )
                list_customer_cameras.remove(camera)
            elif score >= 80:
                traced_cameras.append(
                    (
                        camera,
                        f"{Fore.YELLOW}potential{Style.RESET_ALL}",
                        get_camera_obj(match),
                    )
                )
                list_customer_cameras.remove(camera)
            else:
                traced_cameras.append(
                    (camera, f"{Fore.RED}unsupported{Style.RESET_ALL}", None)
                )

    return traced_cameras


def print_list_data(
    customer_cameras: Dict[str, int],
    traced_cameras: List[Tuple[str, str, Optional[CompatibleModel]]],
):
    """Print and save a formatted list of camera data.

    Args:
        customer_cameras (Dict[str, int]): A dictionary where keys are
            camera names and values are counts.
        traced_cameras
        (List[Tuple[str, str, Optional[CompatibleModel]]]): A list of
            tuples where each tuple contains the camera name, type, and
            an Optional CompatibleModel.
    """
    output = []

    for camera_name, camera_type, matched_camera in traced_cameras:
        camera_count = str(customer_cameras.get(camera_name, 0))

        # Append values to output table
        output.append(
            [
                camera_name,
                camera_count,
                camera_type,
                matched_camera.manufacturer if matched_camera else "",
                matched_camera.model_name if matched_camera else "",
                (
                    matched_camera.minimum_supported_firmware_version
                    if matched_camera
                    else ""
                ),
                matched_camera.notes if matched_camera else "",
            ]
        )

    # Create table headers
    color_headers = [
        f"{Fore.LIGHTBLACK_EX}Camera Name{Style.RESET_ALL}",
        f"{Fore.LIGHTBLACK_EX}Count{Style.RESET_ALL}",
        f"{Fore.LIGHTBLACK_EX}Match Type{Style.RESET_ALL}",
        f"{Fore.LIGHTBLACK_EX}Manufacturer{Style.RESET_ALL}",
        f"{Fore.LIGHTBLACK_EX}Model{Style.RESET_ALL}",
        f"{Fore.LIGHTBLACK_EX}Min Firmware Version{Style.RESET_ALL}",
        f"{Fore.LIGHTBLACK_EX}Notes{Style.RESET_ALL}",
    ]

    plain_headers = [
        "Camera Name",
        "Count",
        "Match Type",
        "Manufacturer",
        "Model",
        "Min Firmware Version",
        "Notes",
    ]
    # Sort alphabetically
    output.sort(key=lambda x: x[2], reverse=True)

    # Print table in pretty format
    print(tabulate(output, headers=color_headers, tablefmt="fancy_grid"))

    # Convert to Pandas DataFrame
    df = pd.DataFrame(
        output,
        columns=plain_headers,
    )
    # Strip color codes
    df["Match Type"] = df["Match Type"].apply(strip_ansi_codes)

    # NOTE: Uncomment to write truncated to terminal
    # print(df.head())

    # NOTE: Uncomment to write to html file
    # df.to_html("camera_models.html", index=False)

    # NOTE: Uncomment to write output to a csv
    # with open("camera_models.txt", "w", encoding="UTF-8") as f:
    #     f.write(
    #         tabulate(
    #             df.values.tolist(), headers=plain_headers, tablefmt="simple"
    #         )
    #     )


def main():
    """
    Main function that orchestrates the compatibility check between
    Verkada cameras and customer cameras. It processes compatibility
    data, identifies camera models, and outputs the matched results.

    This function reads compatibility data from CSV files, identifies the
    relevant camera models from the customer's list, and matches them
    against the Verkada camera list. If a model column is found, it
    retrieves the camera counts and prints the matched camera data;
    otherwise, it notifies the user that the model column could not be
    identified.

    Args:
        None

    Returns:
        None
    """

    verkada_cameras = parse_compatibility_list(
        "Verkada Command Connector Compatibility.csv"
    )
    verkada_cameras_list = get_camera_list(verkada_cameras)
    manufacturers = get_manufacturer_list(verkada_cameras)

    customer_cameras_raw = read_customer_list(
        "./Camera Compatibility Sheets/Axis_edited.csv"
    )

    # NOTE: Uncomment to print raw csv
    # tabulate_data(customer_cameras_raw)

    model_column = identify_model_column(
        customer_cameras_raw, verkada_cameras_list, manufacturers
    )
    if model_column is not None:
        customer_cameras = get_camera_count(model_column, customer_cameras_raw)
        customer_cameras_list = get_camera_list(customer_cameras)

        traced_cameras = camera_match(
            customer_cameras_list,
            verkada_cameras_list,
            verkada_cameras,
            manufacturers,
        )
        print_list_data(customer_cameras, traced_cameras)
    else:
        print(f"{Fore.RED}Could not identify model column.{Style.RESET_ALL}")


# Execute if being ran directly
if __name__ == "__main__":
    main()
