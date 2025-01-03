"""
Author: Ian Young
Purpose: Recommend a Command Connector based on a given site of criteria.
"""

# pylint: disable=ungrouped-imports

# Standard library imports
from typing import List, Optional

# Third-party library imports
import pandas as pd


from app import (
    CompatibleModel,
    Connector,
    log,
    time_function,
    logging_decorator,
)

# Local/application-specific imports
from app.calculations import (
    calculate_4k_storage,
    calculate_excess_channels,
    calculate_low_mp_storage,
    count_mp,
)
from app.memory_management import MemoryStorage


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
        "low_channels": 50,
        "high_channels": 25,
    },
]

# Flips to larger connectors first
REVERSED_COMMAND_CONNECTORS: List[Connector] = sorted(
    COMMAND_CONNECTORS,
    key=lambda x: (x["low_channels"], x["storage"]),
    reverse=True,
)


@time_function
def get_connectors(
    channels: int,
    storage: float,
    recommendation: Optional[List[Connector]] = None,
) -> List[Connector]:
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

    def is_better_connector(
        surplus_channels,
        surplus_storage,
        min_surplus_channels,
        min_surplus_storage,
    ):
        """Helper function to check if the current connector is better."""
        if surplus_channels >= 0 and surplus_storage >= 0:
            if surplus_storage < min_surplus_storage:
                return True
            if (
                surplus_storage == min_surplus_storage
                and surplus_channels < min_surplus_channels
            ):
                return True
        if surplus_channels == 0 and surplus_storage < min_surplus_channels:
            return True
        return False

    log.debug("\n-----Entering iteration-----")
    # Set to zero if negative
    channels = max(channels, 0)
    storage = max(storage, 0)
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

        # Alter values to prefer excess more than deficit
        # Alter Storage
        if 4 < storage < 8:
            storage = 8
        if 8 < storage < 16:
            storage = 16
        if 16 < storage < 32:
            storage = 32

        # Alter channels
        if 10 < channels < 25:
            log.debug("Altering channels")
            channels = 25
        log.debug(channels)
        # Initiate surplus
        surplus_channels = abs(device["low_channels"] - channels)
        surplus_storage = abs(device["storage"] - storage)
        log.debug(device["name"])
        log.debug("%f : %f", min_surplus_channels, surplus_channels)
        log.debug("%f : %f", min_surplus_storage, surplus_storage)
        # Select the connector with the least surplus
        if is_better_connector(
            surplus_channels,
            surplus_storage,
            min_surplus_channels,
            min_surplus_storage,
        ):
            best_connector = device
            log.debug("New device selected as best: %s", best_connector)
            min_surplus_channels = surplus_channels
            min_surplus_storage = surplus_storage

    if best_connector:
        log.debug("Selecting %s to recommend.", best_connector["name"])
        recommendation.append(best_connector)
        # Reduce the remaining channels and storage requirements
        if channels > 0:
            channels -= int(best_connector["low_channels"])
        if storage > 0:
            storage -= int(best_connector["storage"])

        log.debug("Channels: %d", channels)
        # Continue recursing
        return get_connectors(channels, storage, recommendation)

    return recommendation  # Return the list of selected connectors


def recommend_connector(
    low_channels: int,
    high_channels: int,
    storage: float,
    memory: MemoryStorage,
):
    """Formats data and calls recursive function.

    Recommend a connector based on the specified low and high channel
    requirements and storage capacity. This function calculates the total
    required channels and invokes the connector retrieval process.

    Args:
        low_channels (int): The number of low channels required.
        high_channels (int): The number of high channels required.
        storage (float): The amount of storage available.
        memory (MemoryStorage): Class to store frequently accessed variables.

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
    try:
        recommendations = get_connectors(total_required_channels, storage)
    except RecursionError:
        print("Max depth exceeded. Exiting...")
        recommendations = []
    excess_channels = calculate_excess_channels(
        total_required_channels, recommendations
    )
    memory.set_recommendations(recommendations)
    memory.set_excess_channels(excess_channels)
    log.debug(recommendations)
    log.debug("Excess channels: %d", excess_channels)
    # print(", ".join(get_connectors(total_required_channels, storage)))


@logging_decorator
def recommend_connectors(
    change: bool,
    retention: int,
    camera_dataframe: pd.DataFrame,
    verkada_camera_list: List[CompatibleModel],
    memory: MemoryStorage,
) -> None:
    """Driver function to gather all required recursive compute variables.

    Generate connector recommendations based on customer camera data and
    model specifications. This function processes camera counts and
    calculates the required storage for both low and high megapixel
    channels.

    Args:
        change (bool): A Boolean value that indicates whether a change to
            the input has been detected and calculations need to be ran
            again.
        retention (int): The days of required retention for the command
            connector
        camera_dataframe (pd.DataFrame): A dataframe containing customer
            cameras.
        verkada_camera_list (List[CompatibleModel]): A list of verkada
            cameras.
        memory (MemoryStorage): Class to store frequently accessed
            variables.

    Returns:
        None: This function does not return a value but triggers the
            recommendation process for connectors.

    Examples:
        >>> recommend_connectors(camera_dataframe)
    """
    run_calc = (
        not memory.has_recommendations() and not memory.has_excess_channels()
    ) or change
    log.debug("Run calculations: %s", run_calc)
    if run_calc:
        low_mp_count, high_mp_count = count_mp(
            camera_dataframe, verkada_camera_list
        )
        low_storage = calculate_low_mp_storage(low_mp_count, retention)
        high_storage = calculate_4k_storage(high_mp_count, retention)
        total_storage = low_storage + high_storage
        recommend_connector(low_mp_count, high_mp_count, total_storage, memory)
