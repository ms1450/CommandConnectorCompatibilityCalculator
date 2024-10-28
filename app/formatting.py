"""
Author: Mehul Sen
Purpose: The contents of this file are to perform formatting for the
    customer camera file.
"""

# pylint: disable=ungrouped-imports

import os
import re
from collections import defaultdict
from subprocess import check_call
from sys import executable
from typing import Dict, List, Optional, Set

try:
    import pandas as pd
    import colorama
    from colorama import Fore, Style
    from nltk.corpus import words
    from nltk.downloader import download
    from pandas import Series
    from tabulate import tabulate
except ImportError as e:
    package_name = str(e).split()[-1]
    check_call([executable, "-m", "pip", "install", package_name])
    # Import again after installation
    import pandas as pd
    import colorama
    from colorama import Fore, Style
    from nltk.corpus import words
    from nltk.downloader import download
    from pandas import Series
    from tabulate import tabulate


from app import CompatibleModel, Connector, logging_decorator

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


@logging_decorator
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


def ensure_nltk_words_loaded():
    """Ensure the NLTK words corpus is downloaded and available."""
    try:
        if not os.path.isdir(NLTK_DATA_PATH):
            download("words", download_dir=NLTK_DATA_PATH)
        else:
            words.ensure_loaded()
    except LookupError:
        download("words")


def prepare_customer_list(customer_list: pd.DataFrame) -> pd.DataFrame:
    """Handle missing values and strip whitespaces."""
    customer_list = customer_list.fillna("")
    return customer_list.astype(str).apply(lambda x: x.str.strip())


def extract_english_words() -> Set[str]:
    """Extract English words from NLTK corpus."""
    ensure_nltk_words_loaded()
    return {word.lower() for word in words.words()}


def compile_regex_patterns():
    """Compile and return the necessary regex patterns."""
    return {
        "integer": r"^[-+]?\d+$",
        "ip": (
            r"^((25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}"
            r"(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)"
            r"(:\d{1,5})?$"
        ),
        "mac": (
            r"^([0-9A-Fa-f]{2}[:-]){5}[0-9A-Fa-f]{2}$|"
            r"^([0-9A-Fa-f]{4}[:-]){2}[0-9A-Fa-f]{4}$|"
            r"^[0-9A-Fa-f]{12}$"
        ),
        "date": (
            r"^(0?[1-9]|1[0-2])/(0?[1-9]|[12][0-9]|3[01])/(\d{4})$|"
            r"^(0?[1-9]|[12][0-9]|3[01])/(0?[1-9]|1[0-2])/(\d{4})$|"
            r"^\d{4}-(0?[1-9]|1[0-2])-(0?[1-9]|[12][0-9]|3[01])$"
        ),
        "special_char": r'^[/"?\\\-I^&#!%*()~\[\]{}:\'"/\\;,]|II|III|IV$',
        "sequential": r"^#$",
    }


def remove_keywords(
    value: str, dictionary: Set[str], english_words: Set[str], patterns: dict
) -> str:
    """Remove unwanted keywords from a value."""
    if not value:
        return value

    word_set = value.split()
    multiple_words = len(word_set) > 1

    filtered_words = [
        word
        for word in word_set
        if word in dictionary
        or (
            word.lower() not in english_words
            and not any(
                re.match(pattern, word) for pattern in patterns.values()
            )
            and (not multiple_words or not re.match(patterns["integer"], word))
        )
    ]
    return " ".join(filtered_words)


def sanitize_columns(
    sanitized_df: pd.DataFrame, patterns: dict
) -> pd.DataFrame:
    """Remove unwanted columns based on patterns."""
    columns_to_remove = [
        col
        for col in sanitized_df.columns
        if any(
            sanitized_df[col].str.match(pattern).any()
            for pattern in ["ip", "mac", "date"]
        )
    ]

    serial_columns = [
        col
        for col in sanitized_df.columns
        if any(term in col.lower() for term in ["serial", "sn", "s/n"])
    ]
    sequential_columns = [
        col
        for col in sanitized_df.columns
        if re.match(patterns["sequential"], col)
    ]

    sanitized_df = sanitized_df.drop(
        columns=columns_to_remove + serial_columns + sequential_columns
    )
    return sanitized_df


def remove_duplicates_from_row(row) -> pd.Series:
    """Remove duplicate values within a row."""
    seen = set()
    new_row = [
        (
            " ".join(
                [element for element in value.split() if element not in seen]
            )
            if value
            else ""
        )
        for value in row
    ]
    seen.update([el for value in row for el in value.split()])
    if len(new_row) != len(row):
        raise ValueError(f"Length mismatch: {len(new_row)} != {len(row)}")
    return pd.Series(new_row, index=row.index)


def sanitize_customer_data(
    customer_list: pd.DataFrame, dictionary: Set[str]
) -> pd.DataFrame:
    """Sanitize Customer List."""
    customer_list = prepare_customer_list(customer_list)
    english_words = extract_english_words()
    patterns = compile_regex_patterns()

    sanitized_df = customer_list.applymap(
        lambda x: remove_keywords(x, dictionary, english_words, patterns)
    )
    sanitized_df = sanitize_columns(sanitized_df, patterns)
    sanitized_df = sanitized_df.apply(remove_duplicates_from_row, axis=1)

    return sanitized_df.dropna(how="all").dropna(axis=1, how="all")


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


@logging_decorator
def print_connector_recommendation(recommendations: List[Connector]):
    """
    Print a formatted table of device recommendations and their counts.
    This function aggregates the recommendations and displays the results
    in a simple tabular format.

    Args:
        recommendations (List[str]): A list of device recommendations.

    Returns:
        None: This function prints the output directly and does not
            return a value.

    Examples:
        print_connector_recommendation([
            'Device A',
            'Device B',
            'Device A'
        ])
    """

    # Count occurrences of each CC automatically creating keys of 0
    device_count: Dict[str, int] = defaultdict(int)

    for device in recommendations:
        # Add device to dictionary if it doesn't exist and/or increment by one
        device_count[device["name"]] += 1

    # Convert dict to tuple
    device_table = list(device_count.items())

    # NOTE: Uncomment to print recommendations to terminal
    print(
        tabulate(
            device_table,
            headers=["Device", "Count"],
            tablefmt="rounded_outline",
        )
    )


def export_to_csv(df: pd.DataFrame, path: str) -> None:
    """Export a dataframe to a CSV file.

    Args:
        df (pd.DataFrame): The dataframe to export.
        path (str): The path to export the dataframe to.
    """
    if path is not None and path != "":
        df.to_csv(path, index=False)

    # NOTE: Uncomment to output to CSV
    # pd.DataFrame(device_count).to_csv("connector_recommendations.csv")

    # NOTE: Uncomment to output to HTML
    # pd.DataFrame(device_table).to_html("connector_recommendations.html")
