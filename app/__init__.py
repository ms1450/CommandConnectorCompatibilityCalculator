"""Streamline imports across all scripts."""

from typing import TypedDict
from dataclasses import dataclass

from .log import *


@dataclass
class CompatibleModel:
    """Represents a compatible model with its details.

    Args:
        model_name (str): The name of the model.
        manufacturer (str): The manufacturer of the model.
        minimum_supported_firmware_version (str): The minimum firmware
            version that the model supports.
        notes (str): Additional notes regarding the model.

    Attributes:
        channels (int): The number of channels associated with the model,
            initialized to 0.
    """

    model_name: str
    manufacturer: str
    minimum_supported_firmware_version: str
    notes: str
    mp: int = 0
    channels: int = 0


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
