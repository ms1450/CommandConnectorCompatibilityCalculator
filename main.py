"""
Author: Mehul Sen
Co-Author: Ian Young

Purpose: Import a list of third-party cameras and return to the terminal
    which cameras are compatible with the cloud connector.
"""

import colorama
from colorama import Fore, Style

from app.calculations import (
    recommend_connectors,
    identify_model_column,
    get_camera_count,
    get_camera_match,
)
import app.file_handling as fh
from app.formatting import get_camera_set
from app.output import print_results
from app import log

# Initialize colorized output
colorama.init(autoreset=True)

RETENTION = 30  # Required storage in days


def main():
    """
    Main function that orchestrates the compatibility check between
    Verkada cameras and customer cameras. It processes compatibility
    data, identifies camera models, and outputs the matched results.

    This function reads compatibility data from CSV files, identifies the
    relevant camera models from the customer's list, and matches them
    against the Verkada camera list. If a model column is found, it
    retrieves the camera counts and prints the matched camera data;
    otherwise, it notifies the user that the model column could not be
    identified.

    Args:
        None

    Returns:
        None
    """

    verkada_cameras = fh.parse_hardware_compatibility_list(
        "Verkada Command Connector Compatibility.csv"
    )
    verkada_cameras_list = get_camera_set(verkada_cameras)

    customer_cameras_raw = fh.parse_customer_list(
        "./Camera Compatibility Sheets/Camera Compatibility Sheet 5.csv"
    )

    # NOTE: Uncomment to print raw csv
    # tabulate_data(
    #     [customer_cameras_raw.columns.tolist()]
    #     + customer_cameras_raw.T.values.tolist()
    # )

    model_column = identify_model_column(
        customer_cameras_raw, verkada_cameras_list
    )
    if model_column is not None:
        customer_cameras = get_camera_count(model_column, customer_cameras_raw)
        customer_cameras_list = get_camera_set(customer_cameras)
        recommend_connectors(customer_cameras, verkada_cameras_list)
        traced_cameras = get_camera_match(
            customer_cameras_list, verkada_cameras
        )
        print_results(customer_cameras, traced_cameras)
    else:
        log.critical(
            "%sCould not identify model column.%s", Fore.RED, Style.RESET_ALL
        )


# Execute if being ran directly
if __name__ == "__main__":
    main()
