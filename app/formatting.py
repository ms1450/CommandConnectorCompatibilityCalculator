"""
Author: Mehul Sen
Purpose: The contents of this file are to perform formatting for the
    customer camera file.
"""

import os
import re
from typing import List, Optional, Set

import pandas as pd
import colorama
from colorama import Fore, Style
from nltk.corpus import words
from nltk.data import find
from nltk.downloader import download
from pandas import Series
from tabulate import tabulate

from app import CompatibleModel

NLTK_DATA_PATH = "./misc/nltk_data"


# Initialize colorama
colorama.init(autoreset=True)


def get_camera_set(verkada_list: List[CompatibleModel]) -> Set[str]:
    """Retrieve a list of camera names from compatible models.

    Args:
        verkada_list (List[CompatibleModel]): List of compatible models.

    Returns:
        Set[str]: Set of camera names.
    """
    if isinstance(verkada_list, list):
        return {model.model_name for model in verkada_list}
    return {""}


def get_manufacturer_set(verkada_list: List[CompatibleModel]) -> Set[str]:
    """Retrieve a set of camera manufacturer names from compatible models.

    Args:
        verkada_list (List[CompatibleModel]): List of compatible models.

    Returns:
        Set[str]: Set of manufacturer names.
    """
    if isinstance(verkada_list, list):
        return {model.manufacturer.lower() for model in verkada_list}
    return {""}


def find_verkada_camera(
    verkada_model: str, verkada_camera_list: List[CompatibleModel]
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
            for camera in verkada_camera_list
            if camera.model_name.lower() == verkada_model.lower()
        ),
        None,
    )


def list_verkada_camera_details(
    camera_name: Series, verkada_list: List[CompatibleModel]
) -> List[str]:
    """Find a matching camera by its name.

    Args:
        camera_name (str): Name of camera.
        verkada_list (List[CompatibleModel]): List of compatible models.

    Returns:
        List[str]: Matching camera model.
    """
    # Return with next to save memory
    return next(
        (
            (
                [
                    model.model_name,
                    model.manufacturer,
                    model.minimum_supported_firmware_version,
                    "",
                ]
                if model.notes == "nan"
                else [
                    model.model_name,
                    model.manufacturer,
                    model.minimum_supported_firmware_version,
                    model.notes,
                ]
            )
            for model in verkada_list
            if model.model_name == camera_name
        ),
        ["", "", "", ""],
    )


def sanitize_customer_data(
    customer_list: pd.DataFrame, dictionary: Set[str]
) -> pd.DataFrame:
    """Sanitize Customer List: remove whitespace, IPs, MACs, special
    chars, and serial number columns

    Args:
        customer_list (pd.DataFrame): Customer List.
        dictionary (Set[str]): Set of camera names.

    Returns:
        pd.DataFrame: Sanitized Customer List.
    """

    try:
        if not os.path.isdir(NLTK_DATA_PATH):
            download("words", download_dir=NLTK_DATA_PATH)
        else:
            find("corpora/words")
    except LookupError:
        download("words")

    # Handle missing values (replace with empty strings)
    customer_list = customer_list.fillna("")
    # Remove leading/trailing whitespaces
    customer_list = customer_list.astype(str).apply(lambda x: x.str.strip())

    # Extract english words from NLTK
    english_words = {word.lower() for word in words.words()}
    all_keywords = dictionary | english_words

    # Regex Patterns
    integer_pattern = r"^[-+]?\d+$"
    ip_pattern = (
        r"^((25[0-5]|2[0-4][0-9]|"
        r"[01]?[0-9][0-9]?)\.){3}(25[0-5]|"
        r"2[0-4][0-9]|[01]?[0-9][0-9]?)$"
    )
    mac_pattern = (
        r"^([0-9A-Fa-f]{2}[:-]){5}[0-9A-Fa-f]{2}$|"
        r"^([0-9A-Fa-f]{4}[:-]){2}[0-9A-Fa-f]{4}$"
    )
    special_char_pattern = r'^[/"?\\\-I^&#!%*()~\[\]{}:\'"/\\;,]|II|III|IV$'

    def remove_keywords(value: str) -> str:
        if not value:
            return value

        word_set = value.split()

        # Check if there's more than one word
        multiple_words = len(word_set) > 1

        filtered_words = [
            word
            for word in word_set
            if word.lower() not in all_keywords
            and not re.match(ip_pattern, word)
            and not re.match(mac_pattern, word)
            and not re.match(special_char_pattern, word)
            and (not multiple_words or not re.match(integer_pattern, word))
        ]

        return " ".join(filtered_words)

    # Apply the remove_keywords function to all cells
    sanitized_df = customer_list.map(remove_keywords)

    # Remove columns containing IP or MAC addresses
    columns_to_remove = []
    for column in sanitized_df.columns:
        if (
            sanitized_df[column].str.match(ip_pattern).any()
            or sanitized_df[column].str.match(mac_pattern).any()
        ):
            columns_to_remove.append(column)

    # Remove columns with headers containing 'Serial', 'SN', or 'S/N'
    serial_columns = [
        col
        for col in sanitized_df.columns
        if any(term in col.upper() for term in ["SERIAL", "SN", "S/N"])
    ]
    columns_to_remove.extend(serial_columns)
    sanitized_df = sanitized_df.drop(columns=columns_to_remove)

    # Remove empty rows and columns
    sanitized_df = sanitized_df.dropna(how="all").dropna(axis=1, how="all")
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
    print(tabulate(combined_data, headers=headers, tablefmt="pipe"))
