

from colorama import Fore, Style
from tabulate import tabulate
import pandas as pd


def tabulate_data(data: pd.DataFrame) -> None:
    """Tabulate and print the data.

    Args:
        data (List[List[str]]): Transposed data where each list
            represents a column.
    Returns:
        None
    """
    # Extract column names (first element)
    headers = [
        f"{Fore.LIGHTBLACK_EX}{row[0]}{Style.RESET_ALL}" for row in data
    ]

    # Extract data starting from the second element
    table = [row[1:] for row in data]

    # Pair values off
    combined_data = list(zip(*table))

    # Print the tabulated data
    print(tabulate(combined_data, headers=headers, tablefmt="pipe"))


def print_list_data(
    customer_cameras: Dict[str, int],
    traced_cameras: List[Tuple[str, str, Optional[CompatibleModel]]],
):
    """Print and save a formatted list of camera data.

    Args:
        customer_cameras (Dict[str, int]): A dictionary where keys are
            camera names and values are counts.
        traced_cameras
        (List[Tuple[str, str, Optional[CompatibleModel]]]): A list of
            tuples where each tuple contains the camera name, type, and
            an Optional CompatibleModel.
    """
    output = []

    for camera_name, camera_type, matched_camera in traced_cameras:
        camera_count = str(customer_cameras.get(camera_name, 0))

        # Append values to output table
        output.append(
            [
                camera_name,
                camera_count,
                camera_type,
                matched_camera.manufacturer if matched_camera else "",
                matched_camera.model_name if matched_camera else "",
                (
                    matched_camera.minimum_supported_firmware_version
                    if matched_camera
                    else ""
                ),
                matched_camera.notes if matched_camera else "",
            ]
        )

    # Create table headers
    color_headers = [
        f"{Fore.LIGHTBLACK_EX}Camera Name{Style.RESET_ALL}",
        f"{Fore.LIGHTBLACK_EX}Count{Style.RESET_ALL}",
        f"{Fore.LIGHTBLACK_EX}Match Type{Style.RESET_ALL}",
        f"{Fore.LIGHTBLACK_EX}Manufacturer{Style.RESET_ALL}",
        f"{Fore.LIGHTBLACK_EX}Model{Style.RESET_ALL}",
        f"{Fore.LIGHTBLACK_EX}Min Firmware Version{Style.RESET_ALL}",
        f"{Fore.LIGHTBLACK_EX}Notes{Style.RESET_ALL}",
    ]

    plain_headers = [
        "Camera Name",
        "Count",
        "Match Type",
        "Manufacturer",
        "Model",
        "Min Firmware Version",
        "Notes",
    ]

    # Sort alphabetically
    output.sort(key=lambda x: x[2], reverse=True)

    # Print table in pretty format
    print(tabulate(output, headers=color_headers, tablefmt="fancy_grid"))

    # Convert to Pandas DataFrame
    df = pd.DataFrame(
        output,
        columns=plain_headers,
    )
    # Strip color codes
    df["Match Type"] = df["Match Type"].apply(strip_ansi_codes)

    # NOTE: Uncomment to write truncated to terminal
    # print(df.head())
    # NOTE: Uncomment to write to html file
    # df.to_html("camera_models.html", index=False)
    # NOTE: Uncomment to write output to a csv
    # with open("camera_models.txt", "w", encoding="UTF-8") as f:
    #     f.write(
    #         tabulate(
    #             df.values.tolist(), headers=plain_headers, tablefmt="simple"
    #         )
    #     )
