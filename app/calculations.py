"""
Author: Ian Young
Purpose: The contents of this file are to perform various calculations
    to inform the user how many Command Connectors will be required for
    a deal.
"""

from typing import List, Optional, TypedDict


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
