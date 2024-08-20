"""
Author: Mehul Sen
Co-Author: Ian Young

Purpose: Import a list of third-party cameras and return to the terminal
    which cameras are compatible with the cloud connector.
"""

import csv
from typing import Dict, List, Optional, Tuple, Union

import colorama
from colorama import Fore, Style
from tabulate import tabulate
from thefuzz import fuzz, process

# Initialize colorized output
colorama.init(autoreset=True)


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

    def __init__(
        self,
        model_name: str,
        manufacturer: str,
        minimum_supported_firmware_version: str,
        notes: str,
    ):
        self.model_name = model_name
        self.manufacturer = manufacturer
        self.minimum_supported_firmware_version = (
            minimum_supported_firmware_version
        )
        self.notes = notes
        self.channels = 0

    def __str__(self) -> str:
        return self.model_name


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

    elif isinstance(compatible_models, dict):
        return list(compatible_models.keys())

    return []


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

    Args:
        filename (str): The path to the CSV file containing compatibility
            data.

    Returns:
        List[CompatibleModel]: A list of CompatibleModel objects created
            from the CSV data.
    """
    compatible_models = []
    with open(filename, newline="", encoding="UTF-8") as csvfile:
        reader = csv.reader(csvfile, delimiter=",")
        # Skip the first 5 rows
        for _ in range(5):
            next(reader)
        # Read the rest of the rows and create CompatibleModel objects
        for row in reader:
            model = CompatibleModel(row[1].lower(), row[0], row[2], row[3])
            compatible_models.append(model)
    return compatible_models


def read_customer_list(filename: str) -> List[List[str]]:
    """Read a CSV file and transpose its rows into columns.

    Args:
        filename (str): The path to the CSV file containing customer data.

    Returns:
        List[List[str]]: A list of lists, with each inner list
            representing a column from the CSV file.
    """
    with open(filename, newline="", encoding="UTF-8") as csvfile:
        reader = csv.reader(csvfile)
        # Use zip(*reader) to transpose rows into columns
        columns = list(zip(*reader))
    return [list(column) for column in columns]


def tabulate_data(data: List[List[str]]) -> None:
    """Tabulate and print the data.

    Args:
        data (List[List[str]]): Transposed data where each list
            represents a column.
    Returns:
        None
    """
    #! Assuming the columns are in order
    camera_models, direct_comparison, recommended_replacement = data

    # Pair values off
    combined_data = list(
        zip(camera_models, direct_comparison, recommended_replacement)
    )

    # Define headers *REQUIRED*
    headers = [
        f"{Fore.LIGHTBLACK_EX}Camera Model{Style.RESET_ALL}",
        f"{Fore.LIGHTBLACK_EX}Direct Comparison{Style.RESET_ALL}",
        f"{Fore.LIGHTBLACK_EX}Recommended Replacement{Style.RESET_ALL}",
    ]

    # Print the tabulated data
    print(tabulate(combined_data, headers=headers, tablefmt="fancy_grid"))


def identify_model_column(
    customer_cameras_raw: List[List[str]], verkada_cameras_list: List[str]
) -> Optional[int]:
    """Identify the column index that best matches camera models.

    Args:
        customer_cameras_raw (List[List[str]]): Raw customer camera data
            transposed into columns.
        verkada_cameras_list (List[str]): List of known Verkada camera
            model names.

    Returns:
        Optional[int]: The index of the column with the highest match
            score, or None if no valid scores are found.
    """
    scores = []
    for column_data in customer_cameras_raw:
        column_values = set()
        column_score = 0

        for camera in column_data:
            model_name = camera.strip()

            if model_name and model_name not in column_values:
                score = process.extractOne(
                    model_name,
                    verkada_cameras_list,
                    scorer=fuzz.token_sort_ratio,
                )[1]
                column_score += score
                column_values.add(model_name)

        scores.append(column_score)

    if scores:
        return scores.index(max(scores))

    print(
        f"{Fore.RED}No valid scores found."
        f"{Style.RESET_ALL} Check your input data."
    )
    return None


def get_camera_count(
    column_number: int, customer_cameras_raw: List[List[str]]
) -> Dict[str, int]:
    """Count the occurrences of camera names in a specified column.

    Args:
        column_number (int): The index of the column to analyze.
        customer_cameras_raw (List[List[str]]): Raw customer camera data
            transposed into columns.

    Returns:
        Dict[str, int]: A dictionary containing camera names as keys and
            their occurrence counts as values.
    """
    camera_statistics: Dict[str, int] = {}
    for value in customer_cameras_raw[column_number]:
        value = value.strip()
        if value and "model" not in value.lower():
            camera_statistics[value] = camera_statistics.get(value, 0) + 1
    return camera_statistics


def camera_match(
    list_customer_cameras: List[str],
    verkada_cameras_list: List[str],
    verkada_cameras: List[CompatibleModel],
) -> List[Tuple[str, str, Optional[CompatibleModel]]]:
    """Match customer cameras against a list of known Verkada cameras.

    Args:
        list_customer_cameras (List[str]): A list of customer camera names
            to be matched.
        verkada_cameras_list (List[str]): A list of Verkada camera model
            names.
        verkada_cameras (List[CompatibleModel]): A list of CompatibleModel
            objects.

    Returns:
        List[Tuple[str, str, Optional[CompatibleModel]]]: A list of tuples
            where each tuple contains the camera name, match type, and an
            Optional CompatibleModel object.
    """

    def get_camera_obj(camera_name: str) -> Optional[CompatibleModel]:
        return find_matching_camera(camera_name, verkada_cameras)

    traced_cameras = []

    for camera in list_customer_cameras:
        if camera != "":
            match, score = process.extractOne(
                camera, verkada_cameras_list, scorer=fuzz.ratio
            )
            _, sort_score = process.extractOne(
                camera, verkada_cameras_list, scorer=fuzz.token_sort_ratio
            )
            _, set_score = process.extractOne(
                camera, verkada_cameras_list, scorer=fuzz.token_set_ratio
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
    headers = [
        f"{Fore.LIGHTBLACK_EX}Camera Name{Style.RESET_ALL}",
        f"{Fore.LIGHTBLACK_EX}Count{Style.RESET_ALL}",
        f"{Fore.LIGHTBLACK_EX}Match Type{Style.RESET_ALL}",
        f"{Fore.LIGHTBLACK_EX}Manufacturer{Style.RESET_ALL}",
        f"{Fore.LIGHTBLACK_EX}Model{Style.RESET_ALL}",
        f"{Fore.LIGHTBLACK_EX}Min Firmware Version{Style.RESET_ALL}",
        f"{Fore.LIGHTBLACK_EX}Notes{Style.RESET_ALL}",
    ]

    # Sort alphabetically
    output.sort(key=lambda x: x[2], reverse=True)

    # Print table in pretty format
    print(tabulate(output, headers=headers, tablefmt="fancy_grid"))

    # Optionally, save to file (uncomment and adjust if needed)
    # with open("camera_matches.csv", "w", newline="", encoding="UTF-8") as f:
    #     writer = csv.writer(f)
    #     writer.writerow(headers)
    #     writer.writerows(output)


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

    customer_cameras_raw = read_customer_list(
        "./Camera Compatibility Sheets/Camera Compatibility Sheet.csv"
    )

    tabulate_data(customer_cameras_raw)

    model_column = identify_model_column(
        customer_cameras_raw, verkada_cameras_list
    )
    if model_column is not None:
        customer_cameras = get_camera_count(model_column, customer_cameras_raw)
        customer_cameras_list = get_camera_list(customer_cameras)

        traced_cameras = camera_match(
            customer_cameras_list, verkada_cameras_list, verkada_cameras
        )
        print_list_data(customer_cameras, traced_cameras)
    else:
        print(f"{Fore.RED}Could not identify model column.{Style.RESET_ALL}")


# Execute if being ran directly
if __name__ == "__main__":
    main()
