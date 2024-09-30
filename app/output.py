"""
Author: Mehul Sen
Co-Author: Ian Young
Purpose: The contents of this file are to perform output.
"""

import re
from tkinter import Text, END
from typing import List

import pandas as pd
from tabulate import tabulate
from tkinterdnd2 import TkinterDnD

from app import CompatibleModel
from app.formatting import list_verkada_camera_details, strip_ansi_codes


def print_results(
    results: pd.DataFrame,
    verkada_list: List[CompatibleModel],
    text_widget: Text,
    root: TkinterDnD.Tk,
):
    """Print and save a formatted list of camera data.

    Args:
        results (pd.DataFrame): Dataframe containing results of each camera.
        verkada_list (List[CompatibleModel]): List of CompatibleModel objects
        connectors (List[str]): List of Connectors recommended

    Returns:
        None
    """

    color_map = {
        "unsupported": "red",
        "potential": "yellow",
        "identified": "cyan",
        "exact": "green",
    }

    output = []

    # Configure tags for colors
    text_widget.tag_configure("red", foreground="red")
    text_widget.tag_configure("yellow", foreground="yellow")
    text_widget.tag_configure("cyan", foreground="cyan")
    text_widget.tag_configure("green", foreground="green")
    text_widget.tag_configure("lightblack", foreground="lightgray")  # Use light gray as a substitute

    for _, row in results.iterrows():
        camera_data = {
            "camera_name": row["name"],
            "camera_count": int(row["count"]),
            "match_type": row["match_type"],
            "verkada_details": list_verkada_camera_details(
                row["verkada_model"], verkada_list
            ),
        }
        output.append(
            [
                camera_data["camera_name"],
                camera_data["camera_count"],
                camera_data['match_type'],
                *camera_data["verkada_details"],
            ]
        )

    output.sort(key=lambda x: x[2], reverse=True)

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

    # Insert the table into the text widget
    text_widget.config(state="normal")  # Enable editing
    text_widget.delete("1.0", "end")  # Clear previous content

    # Split the table into lines
    for line in table.splitlines():
        # Use regex to split the line based on the vertical bar and strip spaces
        columns = [col.strip() for col in re.split(r'\s*[│]\s*', line) if col.strip()]

        # Debugging output to check split results
        print(f"Processing line: {line}")
        print(f"Columns: {columns}")

        # Skip lines that are entirely separators or headers
        if not columns or re.match(r'^[╒╞╘╤╧╥╨╔╗╚╝╠╣║╬─┼┤┬┴┌┐└┘┏┓┗┛]*$', line):
            continue

        match_type = columns[2] if len(columns) > 2 else ""

        # Determine the color tag
        color_tag = color_map.get(match_type, "lightblack")  # Default to lightblack if not found

        # Insert the line into the text widget with the appropriate color tag
        text_widget.insert("end", line + "\n", color_tag)


    # text_widget.insert("end", table)  # Insert new content
    text_widget.config(state="disabled")  # Make it read-only

    # Set horizontal scrolling
    text_widget.config(wrap="none")

    # Update window width based on the table width
    text_width = (
        max(len(line) for line in table.split("\n")) * 7
    )  # Approximate character width
    window_width = text_width + 20  # Add extra padding of 10 on each side
    root.geometry(f"{window_width}x400")  # Set a fixed height for the window

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
