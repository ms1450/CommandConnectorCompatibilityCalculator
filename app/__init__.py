"""Streamline imports"""

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
    channels: int = 0
