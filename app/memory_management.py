"""
Author: Ian Young
Purpose: Load commonly used variables into a class to avoid unnecessary
compute in the application.
"""

# pylint: disable=ungrouped-imports

# from app.output import gui_creation
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
        self.compatibility_list = None
        self.recommendations = None
        self.excess_channels = None
        self.compatible = None
        self.results = None

    def set_compatibility_list(self, comp):
        """Sets the camera compatibility list into memory.
        
        This function loads the camera compatibility list into memory
        to avoid unnecessary calculations when running the application
        mulitple times before closing the user interface.
        
        Args:
            comp (list): The camera compatibility list to store.
        
        Returns:
            None
        """
        self.compatibility_list = comp

    def set_results(self, results):
        """Sets the results of the camera match algorithm

        This method sets the results of the camera match algorithm.

        Args:
            self: The instance of the class.
            results: The pandas dataframe results of the camera match algorithm.

        Returns:
            None
        """
        self.results = results

    def set_compatibility_list():
        pass

    def get_results(self):
        """Gets the results of the dataframe of the camera match algorithm.

        This method returns the results of the camera match algorithm.

        Args:
            self: The instance of the class.

        Return:
            The results of the memory management operations.
        """
        return self.results

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
        """Gets the dataframe for memory management.

        This method returns the dataframe of camera matches.

        Args:
            self: The instance of the class.

        Returns:
            The dataframe containing the results.
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
