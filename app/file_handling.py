"""
Author: Mehul Sen
Co-Author: Ian Young
Purpose: The contents of this file are to perform file handling.
"""

from typing import List

import pandas as pd

from app import CompatibleModel, time_function


@time_function
def parse_hardware_compatibility_list(filename: str) -> List[CompatibleModel]:
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


@time_function
def parse_customer_list(filename: str) -> pd.DataFrame:
    """Read a CSV file and transpose its rows into columns.

    Args:
        filename (str): The path to the CSV file containing customer data.

    Returns:
        List[List[str]]: A list of lists, with each inner list
            representing a column from the CSV file.
    """

    return pd.read_csv(filename, dtype=str, encoding="UTF-8")
