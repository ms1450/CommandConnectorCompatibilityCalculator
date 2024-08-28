"""
Author: Mehul Sen
Co-Author: Ian Young

Purpose: Import a list of third-party cameras and return to the terminal
    which cameras are compatible with the cloud connector.
"""

import colorama
from colorama import Fore, Style

from app.calculations import (
    get_camera_match,
    compile_camera_mp_channels,
)
from app.file_handling import (
    parse_hardware_compatibility_list,
    parse_customer_list,
)
from app.formatting import sanitize_customer_data, get_manufacturer_set
from app.output import print_results
from app.recommend import recommend_connectors
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

    verkada_compatibility_list = compile_camera_mp_channels(
        parse_hardware_compatibility_list(
            "Verkada Command Connector Compatibility.csv"
        )
    )
    customer_cameras_list = sanitize_customer_data(
        parse_customer_list(
            "./Camera Compatibility Sheets/customer_sheet_1.csv"
        ),
        get_manufacturer_set(verkada_compatibility_list),
    )

    # NOTE: Uncomment to print raw csv
    # tabulate_data(
    #     [customer_cameras_raw.columns.tolist()]
    #     + customer_cameras_raw.T.values.tolist()
    # )

    matched_cameras = get_camera_match(
        customer_cameras_list, verkada_compatibility_list
    )
    if matched_cameras is not None:
        print_results(matched_cameras, verkada_compatibility_list)
        recommend_connectors(matched_cameras, verkada_compatibility_list)
    else:
        log.critical(
            "%sCould not identify model column.%s", Fore.RED, Style.RESET_ALL
        )


# Execute if being run directly
if __name__ == "__main__":
    main()
