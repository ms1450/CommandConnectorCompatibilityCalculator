"""
Author: Mehul Sen
Co-Author: Ian Young
Purpose: The contents of this file are to perform output.
"""

# pylint: disable=ungrouped-imports

from typing import List

import pandas as pd
from tabulate import tabulate

from app import CompatibleModel, log
from app.formatting import list_verkada_camera_details, strip_ansi_codes


def print_results(
    change: bool,
    results: pd.DataFrame,
    verkada_list: List[CompatibleModel],
    memory,
):
    """Print and save a formatted list of camera data.

    Args:
        change (bool): Boolean value that indicates whether a change in
            the input has occurred and calculations need to be ran again.
        results (pd.DataFrame): Dataframe containing results of each camera.
        verkada_list (List[CompatibleModel]): List of CompatibleModel objects
        memory (MemoryStorage): Class to store frequently accessed variables.

    Returns:
        pd.DataFrame: DataFrame containing the formatted camera data if recalculation
        was needed, otherwise None.
    """
    log.debug("Run calculations: %s", (not memory.has_text_widget() or change))

    if not memory.has_text_widget() or change:
        output = []

        for _, row in results.iterrows():
            camera_data = {
                "camera_name": row["name"],
                "camera_count": row["count"],
                "match_type": row["match_type"],
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

        output.sort(key=lambda x: x[2], reverse=False)

        headers = [
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
            columns=headers,
        )

        # Strip color codes
        df["Match Type"] = df["Match Type"].apply(strip_ansi_codes)

        # Generate the table with tabulate
        table = tabulate(output, headers=headers, tablefmt="fancy_grid")
        memory.set_compatible_cameras(table)
        log.info("Compatible cameras set in memory")
        print(table)
        return df
    return None
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
