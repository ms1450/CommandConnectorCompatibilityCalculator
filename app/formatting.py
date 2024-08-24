"""
Author: Mehul Sen
Purpose: The contents of this file are to perform formatting for the customer camera file.
"""

from app import log, CompatibleModel

from typing import List, Optional, Set

import pandas as pd
import re
from nltk.corpus import words


def get_camera_set(
        verkada_list: List[CompatibleModel]
) -> Set[str]:
    """Retrieve a list of camera names from compatible models.

    Args:
        verkada_list (List[CompatibleModel]): List of compatible models.

    Returns:
        Set[str]: Set of camera names.
    """
    if isinstance(verkada_list, list):
        return {model.model_name for model in verkada_list}


def get_manufacturer_set(
        verkada_list: List[CompatibleModel]
) -> Set[str]:
    """Retrieve a set of camera manufacturer names from compatible models.

    Args:
        verkada_list (List[CompatibleModel]): List of compatible models.

    Returns:
        Set[str]: Set of manufacturer names.
    """
    if isinstance(verkada_list, list):
        return {model.manufacturer.lower() for model in verkada_list}


def find_camera_model(
        camera_name: str,
        verkada_list: List[CompatibleModel]
) -> Optional[CompatibleModel]:
    """Find a matching camera by its name.

    Args:
        camera_name (str): Name of camera.
        verkada_list (List[CompatibleModel]): List of compatible models.

    Returns:
        Optional[CompatibleModel]: Matching camera model.
    """
    for model in verkada_list:
        if model.model_name == camera_name:
            return model
    return None


def sanitize_customer_data(
        customer_list: pd.DataFrame,
        dictionary: Set[str]
) -> pd.DataFrame:
    # Handle missing values (replace with empty strings)
    customer_list = customer_list.fillna('')
    # Remove leading/trailing whitespaces
    customer_list = customer_list.astype(str).apply(lambda x: x.str.strip())

    # Extract english words from NLTK
    english_words = set(word.lower() for word in words.words())
    all_keywords = dictionary | english_words

    # Regex Patterns
    integer_pattern = r"^[-+]?\d+$"
    ip_pattern = r"^((25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)$"
    mac_pattern = r"^([0-9A-Fa-f]{2}[:-]){5}[0-9A-Fa-f]{2}$|^([0-9A-Fa-f]{4}[:-]){2}[0-9A-Fa-f]{4}$"
    special_char_pattern = r'^[/"?\\\-I^&#!%*()~\[\]{}:\'"/\\;,]|II|III|IV$'

    def remove_keywords(value: str) -> str:
        if not value:
            return value
        words = value.split()
        filtered_words = [
            word for word in words
            if word.lower() not in all_keywords
            and not re.match(ip_pattern, word)
            and not re.match(mac_pattern, word)
            and not re.match(special_char_pattern, word)
            and not re.match(integer_pattern, word)
        ]
        return ' '.join(filtered_words)

    # Apply the remove_keywords function to all cells
    sanitized_df = customer_list.applymap(remove_keywords)

    # Remove columns containing IP or MAC addresses
    columns_to_remove = []
    for column in sanitized_df.columns:
        if (sanitized_df[column].str.match(ip_pattern).any() or
                sanitized_df[column].str.match(mac_pattern).any()):
            columns_to_remove.append(column)

    # Remove columns with headers containing 'Serial', 'SN', or 'S/N'
    serial_columns = [col for col in sanitized_df.columns if any(term in col.upper() for term in ['SERIAL', 'SN', 'S/N'])]
    columns_to_remove.extend(serial_columns)

    sanitized_df = sanitized_df.drop(columns=columns_to_remove)

    # Remove empty rows and columns
    sanitized_df = sanitized_df.dropna(how='all').dropna(axis=1, how='all')

    return sanitized_df


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



# def santize_customer_list(
#     customer_list: List[List[str]], dictionary: set[str]
# ) -> List[List[str]]:
#     """Santize the supplied list of customers.
#
#     Args:
#         customer_list (List[List[str]]): The list of customers.
#         dictionary (set[str]): The set of customers.
#
#     Returns:
#         List[List[str]]: A list of lists, with each inner list
#     """
#     # Get the set if English words from NLTK
#     english_dictionary = set(word.lower() for word in words.words())
#
#     # Extract Headers and data from the customer_list
#     headers = [row[0] for row in customer_list]
#     data = [row[1:] for row in customer_list]
#
#     def remove_keywords(value: str, keywords: set[str]) -> str:
#         """Remove keywords from the supplied dictionary.
#
#         Args:
#             value (str): The value to remove keywords from.
#             keywords (set[str]): The keywords used to filter the supplied customer list.
#
#         Returns:
#             str: The value with keywords removed.
#         """
#         if not value:
#             return value
#         words = value.strip().split(" ")
#         filtered_words = []
#         for word in words:
#             if word.lower() not in keywords:
#                 if (
#                     not is_ip_address(word)
#                     and not is_mac_address(word)
#                     and not is_special_character(word)
#                     and not is_integer(word)
#                 ):
#                     filtered_words.append(word)
#         return " ".join(filtered_words)
#
#     def is_ip_address(value: str) -> bool:
#         """Check if the given value is a valid IPv4 address.
#
#         Args:
#             value (str): The value to check.
#
#         Returns:
#             bool: True if the value is a valid IPv4 address, False otherwise.
#         """
#         # Regular expression to match IPv4 addresses
#         ip_pattern = re.compile(
#             r"^((25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}"
#             r"(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)$"
#         )
#
#         # Match the pattern and ensure it's a valid IP address
#         return bool(ip_pattern.match(value))
#
#     def contains_ip_address(values: List[str]) -> bool:
#         """Check if the column contains IP addresses.
#
#         Args:
#             values (List[str]): The list of values in the column.
#
#         Returns:
#             bool: True if the column contains IP addresses, False otherwise.
#         """
#         return any(is_ip_address(value) for value in values)
#
#     def is_mac_address(value: str) -> bool:
#         """Check if the given value is a valid MAC address.
#
#         Args:
#             value (str): The value to check.
#
#         Returns:
#             bool: True if the value is a valid MAC address, False otherwise.
#         """
#         mac_pattern = re.compile(
#             r"^([0-9A-Fa-f]{2}[:-]){5}[0-9A-Fa-f]{2}$|^([0-9A-Fa-f]{4}[:-]){2}[0-9A-Fa-f]{4}$"
#         )
#         return bool(mac_pattern.match(value))
#
#     def contains_mac_address(values: List[str]) -> bool:
#         """Check if the column contains MAC addresses.
#
#         Args:
#             values (List[str]): The list of values in the column.
#
#         Returns:
#             bool: True if the column contains IP addresses, False otherwise.
#         """
#         return any(is_mac_address(value) for value in values)
#
#     def remove_ip_mac(
#         headers: List[str], data: List[List[str]]
#     ) -> (List[str], List[List[str]]):
#         """Remove the IP addresses from the supplied headers and data.
#
#         Args:
#             headers (List[str]): The list of headers.
#             data (List[List[List[str]]]): The list of data to be removed.
#
#         Returns:
#             Tuple[List[str], List[List[str]]]: The sanitized headers and data.
#         """
#         columns_to_remove = []
#         for column_index in range(len(headers)):
#             column_values = data[column_index]
#             if contains_ip_address(column_values):
#                 columns_to_remove.append(column_index)
#             if contains_mac_address(column_values):
#                 columns_to_remove.append(column_index)
#         filtered_headers = [
#             header
#             for index, header in enumerate(headers)
#             if index not in columns_to_remove
#         ]
#         filtered_data = [
#             [
#                 value
#                 for index, value in enumerate(row)
#                 if index not in columns_to_remove
#             ]
#             for row in data
#         ]
#         return filtered_headers, filtered_data
#
#     def is_special_character(value: str) -> bool:
#         """Check if the given value is a single special character or a specific sequence.
#
#         Args:
#             value (str): The value to check.
#
#         Returns:
#             bool: True if the value is a special character or specific sequence, False otherwise.
#         """
#         # Define the regex pattern for special characters and sequences
#         special_char_pattern = re.compile(
#             r'^[/"?\\\-I^&#!%*()~\[\]{}:\'"/\\;,]|II|III|IV$'
#         )
#
#         # Match the pattern and return whether it's a valid special character or sequence
#         return bool(special_char_pattern.match(value))
#
#     def is_integer(value: str) -> bool:
#         """Check if the given value is a valid integer using regex.
#
#         Args:
#             value (str): The value to check.
#
#         Returns:
#             bool: True if the value is an integer, False otherwise.
#         """
#         # Define the regex pattern for an integer
#         integer_pattern = re.compile(r"^[-+]?\d+$")
#
#         # Match the pattern and return whether it's a valid integer
#         return bool(integer_pattern.match(value))
#
#     sanitized_data = []
#     for column in data:
#         sanitized_column = []
#         for value in column:
#             sanitized_value = remove_keywords(value, dictionary)
#             sanitized_value = remove_keywords(
#                 sanitized_value, english_dictionary
#             )
#             if (
#                 not is_ip_address(sanitized_value)
#                 and not is_mac_address(sanitized_value)
#                 and not is_special_character(sanitized_value)
#                 and not is_integer(sanitized_value)
#             ):
#                 sanitized_column.append(sanitized_value)
#         sanitized_data.append(sanitized_column)
#     sanitized_headers, sanitized_data = remove_ip_mac(headers, sanitized_data)
#     return [sanitized_headers] + sanitized_data