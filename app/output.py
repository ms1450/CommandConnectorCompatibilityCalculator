"""
Author: Mehul Sen
Co-Author: Ian Young
Purpose: The contents of this file are to perform output.
"""

from typing import List
import colorama
from colorama import Fore, Style
from tabulate import tabulate
import pandas as pd

from app import CompatibleModel
from app.formatting import list_verkada_camera_details, strip_ansi_codes


def print_results(results: pd.DataFrame, verkada_list: List[CompatibleModel]):
    """Print and save a formatted list of camera data.

    Args:
        results (pd.DataFrame): Dataframe containing results of each camera.
        verkada_list (List[CompatibleModel]): List of CompatibleModel objects

    Returns:
        None
    """

    def colorize_type(value):
        if value == "unsupported":
            return f"{Fore.RED}unsupported{Style.RESET_ALL}"
        if value == "potential":
            return f"{Fore.YELLOW}potential{Style.RESET_ALL}"
        if value == "identified":
            return f"{Fore.CYAN}identified{Style.RESET_ALL}"
        if value == "exact":
            return f"{Fore.GREEN}exact{Style.RESET_ALL}"
        return f"{Fore.LIGHTBLACK_EX}{value}{Style.RESET_ALL}"

    # Initialize Colorama
    colorama.init(autoreset=True)

    output = []

    for _, row in results.iterrows():
        camera_data = {
            "camera_name": row["name"],
            "camera_count": int(row["count"]),
            "match_type": colorize_type(row["match_type"]),
            "verkada_details": list_verkada_camera_details(
                row["verkada_model"], verkada_list
            ),
        }
        output.append(
            [
                camera_data["camera_name"],
                camera_data["camera_count"],
                camera_data["match_type"],
                *camera_data["verkada_details"],
            ]
        )

    # Create table headers
    color_headers = [
        f"{Fore.LIGHTBLACK_EX}Camera Name{Style.RESET_ALL}",
        f"{Fore.LIGHTBLACK_EX}Count{Style.RESET_ALL}",
        f"{Fore.LIGHTBLACK_EX}Match Type{Style.RESET_ALL}",
        f"{Fore.LIGHTBLACK_EX}Model{Style.RESET_ALL}",
        f"{Fore.LIGHTBLACK_EX}Manufacturer{Style.RESET_ALL}",
        f"{Fore.LIGHTBLACK_EX}Min Firmware Version{Style.RESET_ALL}",
        f"{Fore.LIGHTBLACK_EX}Notes{Style.RESET_ALL}",
    ]

    output.sort(key=lambda x: x[2], reverse=True)
    print(tabulate(output, headers=color_headers, tablefmt="fancy_grid"))

    plain_headers = [
        "Camera Name",
        "Count",
        "Match Type",
        "Model",
        "Manufacturer",
        "Min Firmware Version",
        "Notes",
    ]

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
