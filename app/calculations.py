"""
Author: Ian Young
Co-Author: Mehul Sen
Purpose: The contents of this file are to perform various calculations
    to inform the user how many Command Connectors will be required for
    a deal.
"""

from typing import Dict, List, Optional, TypedDict

import pandas as pd

import re

from thefuzz import fuzz, process

from app import log, CompatibleModel, formatting


class Connector(TypedDict):
    """
    Typed dictionary that represents a connector with its associated
    attributes. It encapsulates the details of a connector, including its
    name, storage capacity, and channel range.

    This class is used to define the properties of a connector in the
    context of camera compatibility calculations. Each instance of this
    class holds specific information that can be utilized for managing
    connectors and their configurations.

    Attributes:
        name (str): The name of the connector.
        storage (int): The storage capacity of the connector in terabytes.
        low_channels (int): The minimum number of channels supported by
            the connector.
        high_channels (int): The maximum number of channels supported by
            the connector.
    """

    name: str
    storage: int
    low_channels: int
    high_channels: int


# Ensure the dictionaries match the `Connector` TypedDict structure
COMMAND_CONNECTORS: List[Connector] = [
    {
        "name": "CC300-4TB",
        "storage": 4,
        "low_channels": 10,
        "high_channels": 5,
    },
    {
        "name": "CC300-8TB",
        "storage": 8,
        "low_channels": 10,
        "high_channels": 5,
    },
    {
        "name": "CC500-8TB",
        "storage": 8,
        "low_channels": 25,
        "high_channels": 12,
    },
    {
        "name": "CC500-16TB",
        "storage": 16,
        "low_channels": 25,
        "high_channels": 12,
    },
    {
        "name": "CC700-16TB",
        "storage": 16,
        "low_channels": 50,
        "high_channels": 25,
    },
    {
        "name": "CC700-32TB",
        "storage": 32,
        "low_channels": 25,
        "high_channels": 12,
    },
]

# Flips to larger connectors first
REVERSED_COMMAND_CONNECTORS: List[Connector] = sorted(
    COMMAND_CONNECTORS,
    key=lambda x: (x["low_channels"], x["storage"]),
    reverse=True,
)


def compile_low_mp_cameras() -> pd.DataFrame:
    """Compile a DataFrame of cameras with 5 megapixels or fewer.

    This function reads camera specifications from a CSV file and filters
    the data to return only those cameras that have a megapixel rating of
    5 or lower.

    Returns:
        pd.DataFrame: A DataFrame containing camera specifications for
        cameras with 5 megapixels or fewer.

    Raises:
        FileNotFoundError: If the "Camera Specs.csv" file does not exist.

    Examples:
        >>> low_mp_cameras = compile_low_mp_cameras()
        >>> print(low_mp_cameras.head())
              Manufacturer   Model Name   MP  Channels
        0             ACTi          A71  4.0       1.0
        1   Arecont Vision  AV02CID-200  2.1       1.0
        5   Arecont Vision     AV4656DN  4.0       3.0
        6   Arecont Vision     AV4956DN  4.0       2.0
        11        Avigilon   1.0-H3-DC1  1.0       1.0
    """

    camera_map = pd.read_csv("../Camera Specs.csv")
    return camera_map[camera_map["MP"] <= 5]


def compile_high_mp_cameras() -> pd.DataFrame:
    """Compile a DataFrame of cameras with more than 5 megapixels.

    This function reads camera specifications from a CSV file and filters
    the data to return only those cameras that have a megapixel rating of
    more than 5 megapixels.

    Returns:
        pd.DataFrame: A DataFrame containing camera specifications for
        cameras with more than 5 megapixels.

    Raises:
        FileNotFoundError: If the "Camera Specs.csv" file does not exist.

    Examples:
        >>> high_mp_cameras = compile_high_mp_cameras()
        >>> print(high_mp_cameras.head())
             Manufacturer Model Name    MP  Channels
        2  Arecont Vision  AV12176DN  12.0       5.0
        3  Arecont Vision  AV20175DN  20.0       5.0
        4  Arecont Vision  AV20275DN  20.0       4.0
        7  Arecont Vision   AV8185DN   8.0       5.0
        8             Ava   360-W-30  12.0       1.0
    """

    camera_map = pd.read_csv("../Camera Specs.csv")
    return camera_map[camera_map["MP"] > 5]


def count_low_mp_channels(customer_cameras: Dict[str, int]) -> int:
    """Calculate the total number of channels for low megapixel cameras.

    This function takes a dictionary of customer cameras and computes the total
    number of channels for those cameras that are classified as low megapixel.
    It merges the camera data with a predefined list of low megapixel cameras
    and calculates the total channels based on the count of each camera model.

    Args:
        customer_cameras (Dict[str, int]): A dictionary where keys are camera
        model names and values are the counts of each model.

    Returns:
        int: The total number of channels for low megapixel cameras.
    """
    cameras = pd.DataFrame(
        list(customer_cameras.items()), columns=["Model", "Count"]
    )  # Convert to DataFrame
    low_mp_list = compile_low_mp_cameras()
    merged_df = pd.merge(
        cameras, low_mp_list, left_on="Model", right_on="Model Name"
    )

    merged_df["Total Channels"] = merged_df["Count"] * merged_df["Channels"]
    log.debug("Low mp channels:\n%s", merged_df.head())

    return merged_df["Total Channels"].sum()


def count_high_mp_channels(customer_cameras: Dict[str, int]) -> int:
    """Calculate the total number of channels for high megapixel cameras.

    This function takes a dictionary of customer cameras and computes the
    total number of channels for those cameras that are classified as high
    megapixel. It merges the camera data with a predefined list of high
    megapixel cameras and calculates the total channels based on the count
    of each camera model.

    Args:
        customer_cameras (Dict[str, int]): A dictionary where keys are camera
        model names and values are the counts of each model.

    Returns:
        int: The total number of channels for high megapixel cameras.
    """

    cameras = pd.DataFrame(
        list(customer_cameras.items()), columns=["Model", "Count"]
    )  # Convert to DataFrame
    high_mp_list = compile_high_mp_cameras()
    merged_df = pd.merge(
        cameras, high_mp_list, left_on="Model", right_on="Model Name"
    )

    merged_df["Total Channels"] = merged_df["Count"] * merged_df["Channels"]
    log.debug("high mp channels:\n%s", merged_df.head())

    return merged_df["Total Channels"].sum()


def calculate_low_mp_storage(channels: int, retention: int) -> float:
    """
    Calculates the low megapixel storage requirement based on the number
    of channels and the retention period. The function returns the storage
    needed in gigabytes, depending on the specified retention duration.

    This function determines the storage requirement by applying different
    multipliers based on the retention period. It accounts for three
    retention ranges: up to 30 days, up to 60 days, and up to 90 days,
    returning a calculated storage value accordingly.

    Args:
        channels (int): The number of channels for which storage is being
            calculated.
        retention (int): The retention period in days.

    Returns:
        float: The calculated storage requirement in gigabytes, or None if
            the retention is not supported.
    """

    if retention <= 30:
        return channels * 0.256
    if retention <= 60:
        return channels * 0.512
    return channels * 0.768 * 90 if retention <= 90 else 0


def calculate_4k_storage(channels: int, retention: int) -> float:
    """
    Calculates the 4k storage requirement based on the number
    of channels and the retention period. The function returns the storage
    needed in terabytes, depending on the specified retention duration.

    This function determines the storage requirement by applying different
    multipliers based on the retention period. It accounts for three
    retention ranges: up to 30 days, up to 60 days, and up to 90 days,
    returning a calculated storage value accordingly.

    Args:
        channels (int): The number of channels for which storage is being
            calculated.
        retention (int): The retention period in days.

    Returns:
        float: The calculated storage requirement in gigabytes, or None if
            the retention value is not supported.
    """
    if retention <= 30:
        return channels * 0.512 * 30
    if retention <= 60:
        return channels * 1.024 * 60
    return channels * 2.048 * 90 if retention <= 90 else 0


def get_connectors(
    channels: int, storage: float, recommendation: Optional[List[str]] = None
) -> List[str]:
    """
    Retrieve a list of recommended connectors based on available channels
    and storage. This function recursively finds connectors that meet the
    specified requirements until they are satisfied.

    Args:
        channels (int): The number of available channels required.
        storage (int): The amount of storage required.
        recommendation (Optional[List[Connector]], optional): A list to
        accumulate recommended connectors. Defaults to None.

    Returns:
        List[Connector]: A list of connectors that meet the specified
        channels and storage requirements.
    """
    log.debug("\n-----Entering iteration-----")
    log.debug("Channels: %i", channels)
    log.debug("Storage: %0.3f", storage)
    # Base case: Initialize recommendation list
    if recommendation is None:
        log.debug("Initializing recursion.")
        recommendation = []

    # End case: Exit when channels and storage requirements are met
    if channels <= 0 and storage <= 0:
        log.debug("Exiting recursion.")
        return recommendation

    # Set base values assuming nothing is the best solution
    best_connector = None
    min_surplus_channels = float("inf")
    min_surplus_storage = float("inf")

    for device in COMMAND_CONNECTORS:
        surplus_channels = abs(device["low_channels"] - channels)
        surplus_storage = abs(device["storage"] - storage)
        log.debug(device["name"])
        log.debug("%f : %f", min_surplus_channels, surplus_channels)
        log.debug("%f : %f", min_surplus_storage, surplus_storage)
        # Select the connector with the least surplus
        if (
            surplus_channels >= 0
            and surplus_storage >= 0
            and (
                (surplus_storage < min_surplus_storage)
                or (surplus_storage == min_surplus_storage)
                and surplus_channels < min_surplus_channels
            )
        ):
            best_connector = device
            min_surplus_channels = surplus_channels
            min_surplus_storage = surplus_storage

    if best_connector:
        log.debug("Recommending : %s", best_connector["name"])
        recommendation.append(best_connector["name"])
        # Reduce the remaining channels and storage requirements
        if channels > 0:
            channels -= best_connector["low_channels"]
        if storage > 0:
            storage -= best_connector["storage"]

        # Continue recursing
        return get_connectors(channels, storage, recommendation)

    return recommendation  # Return the list of selected connectors


def recommend_connector(low_channels: int, high_channels: int, storage: float):
    """
    Recommend a connector based on the specified low and high channel
    requirements and storage capacity. This function calculates the total
    required channels and invokes the connector retrieval process.

    Args:
        low_channels (int): The number of low channels required.
        high_channels (int): The number of high channels required.
        storage (float): The amount of storage available.

    Returns:
        None: This function does not return a value but calls another
        function to get connectors.

    Examples:
        >>> recommend_connector(2, 3, 10.0)
        CC300-8TB, CC300-4TB
    """
    log.info("Total storage needed: %0.2f", storage)
    total_required_channels = low_channels + high_channels * 2
    log.info("Total channels needed: %i", total_required_channels)
    print(", ".join(get_connectors(total_required_channels, storage)))


def calculate_mp(width, height):
    """
    Calculates the megapixel (MP) value based on the given width and
    height in pixels. The function converts the pixel dimensions into
    megapixels by dividing the total pixel count by one million.

    This function is useful for determining the resolution of an image
    in terms of megapixels, which is a common metric in photography and
    imaging. It takes the width and height as inputs and returns the
    calculated MP value.

    Args:
        width (int): The width of the image in pixels.
        height (int): The height of the image in pixels.

    Returns:
        float: The calculated megapixel value.
    """
    print(f"{width}x{height}")
    return (width * height) / 1000000


def identify_model_column(
        customer_list: pd.DataFrame,
        verkada_cameras: List[CompatibleModel]
) -> Optional[int]:
    verkada_camera_list = formatting.get_camera_set(verkada_cameras)
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
    def calculate_score(column_data):
        column_values = set()
        column_score = 0
        for camera in column_data.dropna():  # Remove NaN values
            if isinstance(camera, str):
                if (
                    camera and camera not in column_values
                ):  # Skip empty strings
                    # Perform fuzzy matching and accumulate the score
                    score = process.extractOne(
                        camera,
                        verkada_camera_list,
                        scorer=fuzz.token_sort_ratio,
                    )[1]
                    column_score += score
        return column_score
    # Apply the score calculation to each column in the DataFrame
    scores = customer_list.apply(calculate_score)
    log.info("Scores: " + scores.to_string())
    # Get the index of the column with the highest score
    if not scores.empty and scores.max() > 0:
        return int(scores.idxmax())
    log.warning(
        "%sNo valid scores found.%s Check your input data."
    )
    return None


def identify_count_column(df: pd.DataFrame) -> Optional[int]:
    """Find the column index for count data using regex

    Args:
        df (Pandas.DataFrame): The DataFrame to search.

    Returns:
        Optional[int]: The index of the count column, or None if not
            present.
    """
    # Case-insensitive pattern to search
    count_column_pattern = re.compile(r"(?i)\bcount\b|#|\bquantity\b")

    return next(
        (
            i
            for i, col in enumerate(df.columns)
            if isinstance(col, str) and count_column_pattern.match(col)
        ),
        None,
    )


def get_camera_count(
    column_number: int, customer_list: pd.DataFrame
) -> Dict[str, int]:
    """Count the occurrences of camera names in a specified column.

    Args:
        column_number (int): The index of the column to analyze.
        customer_list (Pandas.DataFrame): Raw customer camera data
            transposed into columns.

    Returns:
        Dict[str, int]: A dictionary containing camera names as keys and
            their occurrence counts as values.
    """
    # Check if count column exists
    count_column_index = identify_count_column(customer_list)
    camera_statistics: Dict[str, int] = {}
    if count_column_index is not None:
        count_data = customer_list.iloc[:, count_column_index]
        camera_statistics = dict(
            zip(customer_list.iloc[:, 0], count_data)
        )
        # Ensure the counts are integers and handle missing value cases
        return {
            str(name).strip(): 0 if pd.isna(i) or i == "nan" else int(i)
            for name, i in camera_statistics.items()
            if name
        }

    # Default to counting cameras by name
    customer_list.T.values.tolist()
    for value in customer_list[column_number]:
        value = str(value).strip()
        if value and "model" not in value.lower():
            camera_statistics[value] = camera_statistics.get(value, 0) + 1
    return camera_statistics


def get_camera_match(
        customer_list: pd.DataFrame,
        verkada_cameras: List[CompatibleModel]
) -> pd.DataFrame:
    """Match customer cameras against a list of known Verkada cameras."""

    """"""
    def match_camera(camera):
        if pd.isna(camera) or camera == '':
            return pd.Series({'match_type': 'empty', 'verkada_model': None})

        match, score = process.extractOne(camera, verkada_cameras_list, scorer=fuzz.ratio)
        _, sort_score = process.extractOne(camera, verkada_cameras_list, scorer=fuzz.token_sort_ratio)
        _, set_score = process.extractOne(camera, verkada_cameras_list, scorer=fuzz.token_set_ratio)

        if score == 100 or sort_score == 100:
            return pd.Series({'match_type': f"exact", 'verkada_model': match})
        elif set_score == 100:
            return pd.Series({'match_type': f"identified", 'verkada_model': match})
        elif score >= 80:
            return pd.Series({'match_type': f"potential", 'verkada_model': match})
        else:
            return pd.Series({'match_type': f"unsupported", 'verkada_model': None})

    model_column_index = identify_model_column(customer_list, verkada_cameras)
    if model_column_index is None:
        # Handle the case where no suitable column is found
        return customer_list  # or raise an exception

    model_data = customer_list.iloc[:, model_column_index]

    verkada_cameras_list = [str(camera) for camera in verkada_cameras]

    # Apply the matching function to the model data
    result = model_data.apply(match_camera)
    return result


def recommend_connectors(customer_cameras: Dict[str, int]):
    """
    Generate connector recommendations based on customer camera data and
    model specifications. This function processes camera counts and
    calculates the required storage for both low and high megapixel
    channels.

    Args:
        customer_cameras (Dict[str, int]): A list of customer cameras and
            the count of each model.

    Returns:
        None: This function does not return a value but triggers the
            recommendation process for connectors.

    Examples:
        >>> recommend_connectors('model_column_name', raw_camera_data)
    """
    low_mp_count = calc.count_low_mp_channels(customer_cameras)
    low_storage = calc.calculate_low_mp_storage(low_mp_count, RETENTION)

    high_mp_count = calc.count_high_mp_channels(customer_cameras)
    high_storage = calc.calculate_4k_storage(high_mp_count, RETENTION)

    total_storage = low_storage + high_storage
    calc.recommend_connector(low_mp_count, high_mp_count, total_storage)

