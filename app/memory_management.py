"""
Author: Ian Young
Purpose: Load commonly used variables into a class to avoid unnecessary
compute in the application.
"""

# pylint: disable=ungrouped-imports

from subprocess import check_call
from sys import executable
from tkinter import Text

try:
    from tkinterdnd2 import TkinterDnD
except ImportError as e:
    package_name = str(e).split()[-1]
    check_call([executable, "-m", "pip", "install", package_name])
    # Import again after installation
    from tkinterdnd2 import TkinterDnD

from app.output import gui_creation
from app.formatting import print_connector_recommendation


class MemoryStorage:
    """A class to manage memory-related recommendations and configurations.

    This class provides methods to set and retrieve recommendations,
    excess channels, and compatible cameras. It ensures that these
    attributes are properly initialized and accessible for memory
    management operations.

    Attributes:
        recommendations: The recommendations for memory management.
        excess_channels: The number of excess channels available.
        compatible: The compatible cameras for the memory management
            system.
    """

    def __init__(self) -> None:
        """Initializes the memory management class.

        This constructor sets up the initial state of the instance by
        initializing the recommendations, excess channels, and
        compatibility attributes to None. It prepares the instance for
        further operations related to memory management.

        Args:
            self: The instance of the class.

        Returns:
            None
        """
        self.recommendations = None
        self.excess_channels = None
        self.compatible = None

    def set_recommendations(self, recommendations):
        """Sets the recommendations for memory management.

        This method assigns the provided recommendations to the instance
        if they are not already set. It ensures that the recommendations
        are available for future use.

        Args:
            self: The instance of the class.
            recommendations: The recommendations to be set.

        Returns:
            None
        """
        self.recommendations = recommendations

    def get_recommendations(self):
        """Gets the recommendations for memory management.

        This method returns the recommendations for memory management.

        Args:
            self: The instance of the class.

        Returns:
            The recommendations for memory management.
        """
        return self.recommendations

    def set_excess_channels(self, excess_channels):
        """Sets the value of excess channels for memory management.

        This method assigns the provided excess channels to the instance
        if they have not already been initialized. It ensures that the
        excess channels are available for future operations.

        Args:
            self: The instance of the class.
            excess_channels: The value of excess channels to be set.

        Returns:
            None
        """
        self.excess_channels = excess_channels

    def get_excess_channels(self):
        """Gets the value of excess channels for memory management.

        This method returns the value of excess channels for memory management.

        Args:
            self: The instance of the class.

        Returns:
              The value of excess channels for memory management.
        """
        return self.excess_channels

    def set_compatible_cameras(self, compatible):
        """Sets the value of compatible cameras for memory management.

        This method assigns the provided compatible cameras to the
        instance if they have not already been initialized. It ensures
        that the compatible cameras are available for future operations.

        Args:
            self: The instance of the class.
            compatible: The value of compatible cameras to be set.

        Returns:
            None
        """
        self.compatible = compatible

    def has_recommendations(self):
        """Checks if recommendations are available.

        This method returns a boolean indicating whether the
        recommendations attribute is set and not None. It helps determine
        if there are valid recommendations for memory management.

        Args:
            self: The instance of the class.

        Returns:
            bool: True if recommendations exist and are not None, otherwise
                False.
        """
        return self.recommendations is not None

    def has_excess_channels(self):
        """Checks if excess channels are available.

        This method returns a boolean indicating whether the excess_channels
        attribute is set and not None. It helps determine if there are valid
        excess channels for memory management.

        Args:
            self: The instance of the class.

        Returns:
            bool: True if excess channels exist and are not None, otherwise
                False.
        """
        return self.excess_channels is not None

    def has_text_widget(self):
        """Checks if a text widget is available.

        This method returns a boolean indicating whether the compatible
        attribute is set and not None. It helps determine if there is a
        valid text widget for memory management.

        Args:
            self: The instance of the class.

        Returns:
            bool: True if a text widget exists and is not None, otherwise
                False.
        """
        return self.compatible is not None

    def print_recommendations(self):
        """Prints the provided recommendations for memory management.

        This method Prints the connector recommendations.
        It ensures that the recommendations are available for display.

        Args:
            self: The instance of the class.

        Returns:
            None
        """
        print_connector_recommendation(self.recommendations)

    def print_compatible(self, root: TkinterDnD.Tk, text_widget: Text):
        """Displays compatible items in the specified text widget.

        This method utilizes the GUI creation function to present the
        compatible items in the provided text widget within the specified
        root window. It ensures that the compatible items are visually
        represented in the user interface.

        Args:
            self: The instance of the class.
            root (TkinterDnD.Tk): The root window for the GUI.
            text_widget (Text): The text widget where compatible items
                will be displayed.

        Returns:
            None
        """
        gui_creation(self.compatible, root, text_widget)
