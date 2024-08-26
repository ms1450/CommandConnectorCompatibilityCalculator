"""
Author: Mehul Sen
Purpose: The contents of this file are to perform formatting for the customer camera file.
"""

import os
import re
from typing import List, Set
import pandas as pd
import nltk
from pandas import Series
from nltk.corpus import words

from app import CompatibleModel

NLTK_DATA_PATH = "../misc/nltk_data"


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


def get_verkada_camera_details(
    camera_name: Series, verkada_list: List[CompatibleModel]
) -> List[str]:
    """Find a matching camera by its name.

    Args:
        camera_name (str): Name of camera.
        verkada_list (List[CompatibleModel]): List of compatible models.

    Returns:
        List[str]: Matching camera model.
    """
    for model in verkada_list:
        if model.model_name == camera_name:
            if model.notes == "nan":
                return [
                    model.model_name,
                    model.manufacturer,
                    model.minimum_supported_firmware_version,
                    "",
                ]
            return [
                model.model_name,
                model.manufacturer,
                model.minimum_supported_firmware_version,
                model.notes,
            ]
    return ["", "", "", ""]


def sanitize_customer_data(
    customer_list: pd.DataFrame, dictionary: Set[str]
) -> pd.DataFrame:
    """Sanitize Customer List: remove whitespace, IPs, MACs, special chars, and serial number columns

    Args:
        customer_list (pd.DataFrame): Customer List.
        dictionary (Set[str]): Set of camera names.

    Returns:
        pd.DataFrame: Sanitized Customer List.
    """

    if not os.path.isdir(NLTK_DATA_PATH):
        nltk.download("words", download_dir=NLTK_DATA_PATH)
    else:
        nltk.data.find("corpora/words")

    # Handle missing values (replace with empty strings)
    customer_list = customer_list.fillna("")
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
