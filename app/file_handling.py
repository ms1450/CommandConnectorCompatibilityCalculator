"""
Author: Mehul Sen
Co-Author: Ian Young
Purpose: The contents of this file are to perform file handling.
"""


from typing import List
import pandas as pd
from app import CompatibleModel


def parse_hardware_compatibility_list(filename: str) -> List[CompatibleModel]:
    """Parses the hardware compatibility list from a file.

    Args:
        filename (str): The name of the file containing the hardware compatibility list.

    Returns:
        List[CompatibleModel]: A list of compatible models.
    """

    compatible_models = []
    # Read the CSV file, skipping the first 5 rows and using no header
    df = pd.read_csv(filename, skiprows=5, header=None, encoding="UTF-8")

    # Ensure that the DataFrame has at least 4 columns
    if df.shape[1] < 4:
        raise ValueError(
            "CSV file does not have the expected number of columns."
        )

    # Iterate over each row in the DataFrame
    for _, row in df.iterrows():
        if len(row) < 4:
            continue  # Skip rows that do not have enough columns

        # Create a CompatibleModel instance from the row data
        model = CompatibleModel(
            model_name=row[1].lower(),
            manufacturer=str(row[0]),
            minimum_supported_firmware_version=str(row[2]),
            notes=str(row[3]),
        )
        compatible_models.append(model)
    return compatible_models


def parse_customer_list(filename: str) -> pd.DataFrame:
    """Read a CSV file and transpose its rows into columns.

    Args:
        filename (str): The path to the CSV file containing customer data.

    Returns:
        List[List[str]]: A list of lists, with each inner list
            representing a column from the CSV file.
    """

    return pd.read_csv(filename, dtype=str, encoding="UTF-8")
