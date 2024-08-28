"""
Author: Ian Young
Purpose: Recommend a Command Connector based on a given site of criteria.
"""

# Standard library imports
from typing import List, Optional, TypedDict

# Third-party library imports
import pandas as pd

# Local/application-specific imports
from app.calculations import (
    calculate_4k_storage,
    calculate_low_mp_storage,
    count_mp,
)
from app.formatting import print_connector_recommendation
from app import CompatibleModel, log

RETENTION = 30  # Required storage in days


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


def get_connectors(
    channels: int, storage: float, recommendation: Optional[List[str]] = None
) -> List[str]:
    """Recursive function to recommend a Command Connector.

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
    """Formats data and calls recursive function.

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
    print_connector_recommendation(
        get_connectors(total_required_channels, storage)
    )
    # print(", ".join(get_connectors(total_required_channels, storage)))


def recommend_connectors(
    camera_dataframe: pd.DataFrame, verkada_camera_list: List[CompatibleModel]
):
    """Driver function to gather all required recursive compute variables.

    Generate connector recommendations based on customer camera data and
    model specifications. This function processes camera counts and
    calculates the required storage for both low and high megapixel
    channels.

    Args:
        camera_dataframe (pd.DataFrame): A dataframe containing customer cameras
        verkada_camera_list (List[CompatibleModel]): A list of verkada cameras

    Returns:
        None: This function does not return a value but triggers the
            recommendation process for connectors.

    Examples:
        >>> recommend_connectors(camera_dataframe)
    """
    low_mp_count, high_mp_count = count_mp(
        camera_dataframe, verkada_camera_list
    )
    low_storage = calculate_low_mp_storage(low_mp_count, RETENTION)
    high_storage = calculate_4k_storage(high_mp_count, RETENTION)
    total_storage = low_storage + high_storage
    recommend_connector(low_mp_count, high_mp_count, total_storage)