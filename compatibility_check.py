"""
Author: Mehul Sen
Co-Author: Ian Young

Purpose: Import a list of third-party cameras and return to the terminal
    which cameras are compatible with the cloud connector.
"""

import csv
import re
import nltk
from nltk.corpus import words
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple, Union

import colorama
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
    manufacturers: set[str] = set()
    if isinstance(compatible_models, list):
        return {model.manufacturer.lower() for model in compatible_models}
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


def santize_customer_list(
    customer_list: List[List[str]], dictionary: set[str]
) -> List[List[str]]:
    """Santize the supplied list of customers.

    Args:
        customer_list (List[List[str]]): The list of customers.
        dictionary (set[str]): The set of customers.

    Returns:
        List[List[str]]: A list of lists, with each inner list
    """
    # Get the set if English words from NLTK
    english_dictionary = set(word.lower() for word in words.words())

    # Extract Headers and data from the customer_list
    headers = [row[0] for row in customer_list]
    data = [row[1:] for row in customer_list]

    def remove_keywords(value: str, keywords: set[str]) -> str:
        """Remove keywords from the supplied dictionary.

        Args:
            value (str): The value to remove keywords from.
            keywords (set[str]): The keywords used to filter the supplied customer list.

        Returns:
            str: The value with keywords removed.
        """
        if not value:
            return value
        words = value.strip().split(" ")
        filtered_words = []
        for word in words:
            if word.lower() not in keywords:
                if (
                    not is_ip_address(word)
                    and not is_mac_address(word)
                    and not is_special_character(word)
                    and not is_integer(word)
                ):
                    filtered_words.append(word)
        return " ".join(filtered_words)

    def is_ip_address(value: str) -> bool:
        """Check if the given value is a valid IPv4 address.

        Args:
            value (str): The value to check.

        Returns:
            bool: True if the value is a valid IPv4 address, False otherwise.
        """
        # Regular expression to match IPv4 addresses
        ip_pattern = re.compile(
            r"^((25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}"
            r"(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)$"
        )

        # Match the pattern and ensure it's a valid IP address
        return bool(ip_pattern.match(value))

    def contains_ip_address(values: List[str]) -> bool:
        """Check if the column contains IP addresses.

        Args:
            values (List[str]): The list of values in the column.

        Returns:
            bool: True if the column contains IP addresses, False otherwise.
        """
        return any(is_ip_address(value) for value in values)

    def is_mac_address(value: str) -> bool:
        """Check if the given value is a valid MAC address.

        Args:
            value (str): The value to check.

        Returns:
            bool: True if the value is a valid MAC address, False otherwise.
        """
        mac_pattern = re.compile(
            r"^([0-9A-Fa-f]{2}[:-]){5}[0-9A-Fa-f]{2}$|^([0-9A-Fa-f]{4}[:-]){2}[0-9A-Fa-f]{4}$"
        )
        return bool(mac_pattern.match(value))

    def contains_mac_address(values: List[str]) -> bool:
        """Check if the column contains MAC addresses.

        Args:
            values (List[str]): The list of values in the column.

        Returns:
            bool: True if the column contains IP addresses, False otherwise.
        """
        return any(is_mac_address(value) for value in values)

    def remove_ip_mac(
        headers: List[str], data: List[List[str]]
    ) -> (List[str], List[List[str]]):
        """Remove the IP addresses from the supplied headers and data.

        Args:
            headers (List[str]): The list of headers.
            data (List[List[List[str]]]): The list of data to be removed.

        Returns:
            Tuple[List[str], List[List[str]]]: The sanitized headers and data.
        """
        columns_to_remove = []
        for column_index in range(len(headers)):
            column_values = data[column_index]
            if contains_ip_address(column_values):
                columns_to_remove.append(column_index)
            if contains_mac_address(column_values):
                columns_to_remove.append(column_index)
        filtered_headers = [
            header
            for index, header in enumerate(headers)
            if index not in columns_to_remove
        ]
        filtered_data = [
            [
                value
                for index, value in enumerate(row)
                if index not in columns_to_remove
            ]
            for row in data
        ]
        return filtered_headers, filtered_data

    def is_special_character(value: str) -> bool:
        """Check if the given value is a single special character or a specific sequence.

        Args:
            value (str): The value to check.

        Returns:
            bool: True if the value is a special character or specific sequence, False otherwise.
        """
        # Define the regex pattern for special characters and sequences
        special_char_pattern = re.compile(
            r'^[/"?\\\-I^&#!%*()~\[\]{}:\'"/\\;,]|II|III|IV$'
        )

        # Match the pattern and return whether it's a valid special character or sequence
        return bool(special_char_pattern.match(value))

    def is_integer(value: str) -> bool:
        """Check if the given value is a valid integer using regex.

        Args:
            value (str): The value to check.

        Returns:
            bool: True if the value is an integer, False otherwise.
        """
        # Define the regex pattern for an integer
        integer_pattern = re.compile(r"^[-+]?\d+$")

        # Match the pattern and return whether it's a valid integer
        return bool(integer_pattern.match(value))

    sanitized_data = []
    for column in data:
        sanitized_column = []
        for value in column:
            sanitized_value = remove_keywords(value, dictionary)
            sanitized_value = remove_keywords(
                sanitized_value, english_dictionary
            )
            if (
                not is_ip_address(sanitized_value)
                and not is_mac_address(sanitized_value)
                and not is_special_character(sanitized_value)
                and not is_integer(sanitized_value)
            ):
                sanitized_column.append(sanitized_value)
        sanitized_data.append(sanitized_column)
    sanitized_headers, sanitized_data = remove_ip_mac(headers, sanitized_data)
    return [sanitized_headers] + sanitized_data


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
    if " " in model_name:
        substrings = model_name.split(" ")
        filtered_substrings = [
            sub for sub in substrings if sub.lower() not in manufacturers
        ]
        remaining_string = " ".join(filtered_substrings)
        return remaining_string
    else:
        return model_name


def identify_model_column(
    customer_cameras_raw: List[List[str]],
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
    scores = []
    for column_data in customer_cameras_raw:
        column_values = set()
        column_score = 0

        for camera in column_data:
            model_name = manufacturer_removed(
                camera.strip(), manufacturer_list
            )
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
        print(scores)
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
    nltk.download("words")
    verkada_cameras = parse_compatibility_list(
        "Verkada Command Connector Compatibility.csv"
    )
    verkada_cameras_list = get_camera_list(verkada_cameras)
    manufacturers = get_manufacturer_list(verkada_cameras)

    customer_cameras_raw = read_customer_list(
        "Camera Compatibility Sheets/Private/private 1.csv"
    )
    customer_cameras_raw = santize_customer_list(
        customer_cameras_raw, manufacturers
    )
    # tabulate_data(customer_cameras_raw)

    model_column = identify_model_column(
        customer_cameras_raw, verkada_cameras_list, manufacturers
    )
    print(model_column)
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
