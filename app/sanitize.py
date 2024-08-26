"""
Author: Mehul Sen
Purpose: Runs various logical checks to clean imported data.
"""

import re
from typing import List, Tuple


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
    cleaned_words = value.strip().split(" ")
    filtered_words = [
        word
        for word in cleaned_words
        if word.lower() not in keywords
        and (
            not is_ip_address(word)
            and not is_mac_address(word)
            and not is_special_character(word)
            and not is_integer(word)
        )
    ]
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
) -> Tuple[List[str], List[List[str]]]:
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
