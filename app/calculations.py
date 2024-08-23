"""
Author: Ian Young
Purpose: The contents of this file are to perform various calculations
    to inform the user how many Command Connectors will be required for
    a deal.
"""

from typing import Dict, List, Optional, TypedDict

import pandas as pd

from app import log


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
        storage (int): The storage capacity of the connector in gigabytes.
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


def compile_low_mp_cameras() -> pd.DataFrame:
    """Compile a DataFrame of cameras with 5 megapixels or less.

    This function reads camera specifications from a CSV file and filters
    the data to return only those cameras that have a megapixel rating of
    5 or lower.

    Returns:
        pd.DataFrame: A DataFrame containing camera specifications for
        cameras with 5 megapixels or less.

    Raises:
        FileNotFoundError: If the "Camera Specs.csv" file does not exist.

    Examples:
        >>> low_mp_cameras = compile_low_mp_cameras()
        >>> print(low_mp_cameras)
    """

    camera_map = pd.read_csv("Camera Specs.csv")
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
        >>> low_mp_cameras = compile_high_mp_cameras()
        >>> print(high_mp_cameras)
    """

    camera_map = pd.read_csv("Camera Specs.csv")
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
    log.debug("\n%s", merged_df.head())

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
    log.debug("\n%s", merged_df.head())

    return merged_df["Total Channels"].sum()


def calculate_low_mp_storage(channels: int, retention: int) -> Optional[float]:
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
        return channels * 0.256 * 30
    if retention <= 60:
        return channels * 0.512 * 60
    return channels * 0.768 * 90 if retention <= 90 else None


def calculate_4k_storage(channels: int, retention: int) -> Optional[float]:
    """
    Calculates the 4k storage requirement based on the number
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
            the retention value is not supported.
    """
    if retention <= 30:
        return channels * 0.512 * 30
    if retention <= 60:
        return channels * 1.024 * 60
    return channels * 2.048 * 90 if retention <= 90 else None


def recommend_connector(
    low_channels: int, high_channels: int, storage: float
) -> Optional[str]:
    """
    Recommends a suitable connector based on the specified channel
    requirements and storage capacity. The function evaluates a predefined
    list of connectors and returns the name of the first connector that
    meets the criteria.

    This function calculates the total required channels and checks each
    connector in the list to see if it satisfies the storage and channel
    constraints. If a suitable connector is found, its name is returned;
    otherwise, the function returns None.

    Args:
        low_channels (int): The minimum number of low channels required.
        high_channels (int): The minimum number of high channels required.
        storage (float): The minimum storage capacity required in
            terabytes.

    Returns:
        Optional[str]: The name of the recommended connector, or None if
            no suitable connector is found.
    """

    total_required_channels = low_channels + high_channels * 2
    log.debug("Total channels: %d", total_required_channels)
    return next(
        (
            device["name"]
            for device in COMMAND_CONNECTORS
            if (
                device["storage"] >= storage
                and device["low_channels"] >= low_channels
                and device["high_channels"] >= high_channels
                and device["low_channels"] >= total_required_channels
            )
        ),
        None,
    )


def calculate_mp(width: int, height: int) -> float:
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
    log.info("%ix%i", width, height)
    return (width * height) / 1000000
