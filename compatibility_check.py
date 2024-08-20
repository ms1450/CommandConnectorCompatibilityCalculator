"""
Author: Mehul Sen
Co-Author: Ian Young

Purpose: Import a list of third-party cameras and return to the terminal
    which cameras are compatible with the cloud connector.
"""

# [ ] TODO: Convert to Pandas
# [x] TODO: Move away from global variables
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

    This class stores information about a specific model, including its
    name, manufacturer, minimum supported firmware version, and any
    additional notes. It also tracks the number of channels.

    Args:
        model_name (str): The name of the model.
        manufacturer (str): The manufacturer of the model.
        minimum_supported_firmware_version (str): The minimum firmware
            version that the model supports.
        notes (str): Additional notes regarding the model.

    Attributes:
        channels (int): The number of channels associated with the model,
            initialized to 0.

    Examples:
        model = CompatibleModel(
            "Model X",
            "Manufacturer Y",
            "1.0.0",
            "Some notes"
        )
        print(model)  # Output: Model X
    """

    def __init__(
        self,
        model_name,
        manufacturer,
        minimum_supported_firmware_version,
        notes,
    ):
        self.model_name = model_name
        self.manufacturer = manufacturer
        self.minimum_supported_firmware_version = (
            minimum_supported_firmware_version
        )
        self.notes = notes
        self.channels = 0

    def __str__(self):
        return self.model_name


def get_camera_list(compatible_models: Union[List, Dict]) -> List[str]:
    """Retrieve a list of camera names from compatible models.

    This function extracts camera names from a list of model objects or
    returns the keys from a dictionary of models. It handles both input
    types and returns an empty list if the input is neither.

    Args:
        compatible_models (list or dict): A list of model objects or a
            dictionary of models.

    Returns:
        list: A list of camera names or model keys, or an empty list if
            the input is invalid.
    """
    if isinstance(compatible_models, list):
        return [model.model_name for model in compatible_models]

    elif isinstance(compatible_models, dict):
        return list(compatible_models.keys())


def find_matching_camera(
    camera_name: str, verkada_cameras: List[CompatibleModel]
):
    """Find a matching camera by its name.

    This function searches for a camera in the global list of Verkada
    cameras based on the provided camera name. It returns the camera
    object if a match is found, or None if no match exists.

    Args:
        camera_name (str): The name of the camera to search for.

    Returns:
        object or None: The matching camera object if found, otherwise
            None.
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
    with open(filename, newline="", encoding="UTF-8") as csvfile:
        reader = csv.reader(csvfile)
        # Use zip(*reader) to transpose rows into columns
        columns = list(zip(*reader))
    # Convert each column from tuple to list
    return [list(column) for column in columns]


def identify_model_column(
    customer_cameras_raw: List[List[str]],
    verkada_cameras_list: List[CompatibleModel],
) -> Optional[int]:
    """Identify the column index that best matches camera models.

    This function evaluates each column of raw customer camera data
    against a list of known Verkada cameras, calculating a score based on
    the similarity of the values. It returns the index of the column with
    the highest score, or None if no valid scores are found.

    Returns:
        int or None: The index of the column with the highest match score,
            or None if no valid scores are found.
    """
    # Convert Verkada camera list to a list of model names
    verkada_model_names = [
        camera.model_name for camera in verkada_cameras_list
    ]

    scores = []
    for column_data in customer_cameras_raw:
        column_values = []
        column_score = 0

        for camera in column_data:
            model_name = camera

            if model_name in column_values:
                continue
            elif (
                model_name.strip()
            ):  # Check if value is not empty after stripping whitespace
                # Match the model name against the Verkada model names
                score = process.extractOne(
                    model_name,
                    verkada_model_names,
                    scorer=fuzz.token_sort_ratio,
                )[1]
                column_score += score
                column_values.append(model_name)

        scores.append(column_score)

    if scores:
        return scores.index(max(scores))

    print(
        f"{Fore.RED}No valid scores found.{Style.RESET_ALL} Check your input data."
    )
    return None


def get_camera_count(
    column_number: int, customer_cameras_raw: List[List[str]]
) -> Dict[str, int]:
    """Count the occurrences of camera names in a specified column.

    This function analyzes a specific column of customer camera data,
    counting how many times each camera name appears, while ignoring any
    entries that contain the word "model". It returns a dictionary with
    camera names as keys and their respective counts as values.

    Args:
        column_number (int): The index of the column to analyze.

    Returns:
        dict: A dictionary containing camera names as keys and their
            occurrence counts as values.
    """
    camera_statistics = {}
    for value in customer_cameras_raw[column_number]:
        # Skip this value if it contains 'model' (case-insensitive)
        if "model" in value.lower():
            continue

        # Strip leading and tailing whitespace
        if value := value.strip():
            if value not in camera_statistics:
                camera_statistics[value] = 1
            else:
                camera_statistics[value] += 1
    return camera_statistics


def camera_match(
    list_customer_cameras: List[str],
    verkada_cameras_list: List[str],
    verkada_cameras: List[CompatibleModel],
) -> List[Tuple[str, str, str]]:
    """Match customer cameras against a list of known Verkada cameras.

    This function evaluates a list of customer camera names, attempting
    to find matches in the global list of Verkada cameras using various
    scoring methods. It categorizes each camera as "exact", "identified",
    "potential", or "unsupported" based on the match quality and updates
    the list of customer cameras accordingly.

    Args:
        list_customer_cameras (list): A list of customer camera names to
            be matched.

    Returns:
        None: The function modifies the global state by updating the
            traced_cameras list.
    """

    def get_camera_name(camera_obj: Optional[CompatibleModel]) -> str:
        return camera_obj.model_name if camera_obj is not None else ""

    traced_cameras = []

    for camera in list_customer_cameras:
        if camera != "":
            match, score, _ = process.extractOne(
                camera, verkada_cameras_list, scorer=fuzz.ratio
            )
            _, sort_score, _ = process.extractOne(
                camera, verkada_cameras_list, scorer=fuzz.token_sort_ratio
            )
            _, set_score, _ = process.extractOne(
                camera, verkada_cameras_list, scorer=fuzz.token_set_ratio
            )
            if score == 100 or sort_score == 100:
                traced_cameras.append(
                    (
                        camera,
                        "exact",
                        get_camera_name(
                            find_matching_camera(camera, verkada_cameras)
                        ),
                    )
                )
                list_customer_cameras.remove(camera)
                continue

            if set_score == 100:
                traced_cameras.append(
                    (
                        camera,
                        "identified",
                        get_camera_name(
                            find_matching_camera(match, verkada_cameras)
                        ),
                    )
                )
                list_customer_cameras.remove(camera)
            elif score >= 80:
                traced_cameras.append(
                    (
                        camera,
                        "potential",
                        get_camera_name(
                            find_matching_camera(match, verkada_cameras)
                        ),
                    )
                )
                list_customer_cameras.remove(camera)
            else:
                traced_cameras.append((camera, "unsupported", ""))

    return traced_cameras


def print_list_data(
    customer_cameras: Dict[str, int],
    traced_cameras: List[Tuple[str, str, str]],
):
    """Print and save a formatted list of camera data.

    This function compiles data from the global lists of traced cameras
    and customer cameras, formatting it for display and saving it to a
    text file. It organizes the data by camera type and includes relevant
    details such as manufacturer, model, and firmware version.

    Returns:
        None: The function outputs the formatted data to the console and
        writes it to a file named "camera_models.txt".
    """
    output = []
    for camera_data in traced_cameras:
        camera_name, camera_type, matched_camera = camera_data
        camera_count = str(customer_cameras.get(camera_name, 0))
        if isinstance(matched_camera, CompatibleModel):
            output.append(
                [
                    camera_name,
                    camera_count,
                    camera_type,
                    matched_camera.manufacturer,
                    matched_camera.model_name,
                    matched_camera.minimum_supported_firmware_version,
                    matched_camera.notes,
                ]
            )
        else:
            output.append(
                [camera_name, camera_count, camera_type, "", "", "", ""]
            )

    # Define a custom sorting key
    def sort_key(item):
        order = {"exact": 0, "identified": 1, "potential": 2, "unsupported": 3}
        return order.get(item[2], 4)  # Default to 4 if type is unknown

    # Sort the output list based on the custom sorting key
    output.sort(key=sort_key)

    print(Fore.LIGHTBLACK_EX)  # Set color to gray
    print(
        tabulate(
            output,
            headers=[
                "Camera Name",
                "Camera Count",
                "Supported Type",
                "Manufacturer",
                "Model",
                "Firmware",
                "Additional Notes",
            ],
        )
    )
    print(Style.RESET_ALL)  # Reset the color

    with open("camera_models.txt", "w", encoding="UTF-8") as f:
        f.write(
            tabulate(
                output,
                headers=[
                    "Camera Name",
                    "Camera Count",
                    "Supported Type",
                    "Manufacturer",
                    "Model",
                    "Firmware",
                    "Additional Notes",
                ],
            )
        )


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
    verkada_cameras_list = [
        camera.model_name for camera in get_camera_list(verkada_cameras)
    ]

    customer_cameras_raw = read_customer_list(
        "./Camera Compatibility Sheets/Camera Compatibility Sheet.csv"
    )

    print(customer_cameras_raw)

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
