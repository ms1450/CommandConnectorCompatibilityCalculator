"""
Author: Mehul Sen
Co-Author: Ian Young
Purpose: The contents of this file are to perform output.
"""

import re
from tkinter import Text
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
        text_widget (Text): The text widget where the table will be
            displayed.
        root (TkinterDnD.Tk): The root window of the application.

    Returns:
        None
    """

    output = []

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

    gui_creation(table, root, text_widget)

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


def gui_creation(table, root: TkinterDnD.Tk, text_widget: Text):
    """
    Creates a GUI representation of a table widget with colored entries.

    This function configures the text widget to display the table content
    with specific colors based on the type of data.

    Args:
        table (str): The table content as a string, where each line
            represents a row.
        root (TkinterDnD.Tk): The root window of the application.
        text_widget (Text): The text widget where the table will be
            displayed.

    Returns:
        None

    Examples:
        gui_creation("Row 1\nRow 2", root, text_widget)
    """

    color_map = {
        "unsupported": "red",
        "potential": "yellow",
        "identified": "cyan",
        "exact": "green",
    }

    # Configure tags for colors
    text_widget.tag_configure("red", foreground="red")
    text_widget.tag_configure("yellow", foreground="yellow")
    text_widget.tag_configure("cyan", foreground="cyan")
    text_widget.tag_configure("green", foreground="green")
    text_widget.tag_configure(
        "lightblack", foreground="lightgray"
    )  # Use light gray as a substitute

    # Insert the table into the text widget
    text_widget.config(state="normal")  # Enable editing
    text_widget.delete("1.0", "end")  # Clear previous content

    # Assuming color_map and text_widget are already defined
    for line in table.splitlines():
        # Skip lines that are entirely separators or headers
        if not line.strip() or re.match(
            r"^[╒╞╘╤╧╥╨╔╗╚╝╠╣║╬─┼┤┬┴┌┐└┘┏┓┗┛]*$", line
        ):
            text_widget.insert("end", line + "\n")  # Keep the formatting
            continue

        words = line.split(" ")

        # Insert colorized words while preserving formatting
        for word in words:
            # Strip any surrounding whitespace for matching
            stripped_word = word.strip()
            match_type = stripped_word if stripped_word in color_map else ""

            # Determine the color tag
            color_tag = color_map.get(
                match_type, "lightblack"
            )  # Default to lightblack if not found

            # Insert the word into the text widget with the appropriate color tag
            text_widget.insert(
                "end", stripped_word + " ", color_tag
            )  # Add a space after each word

        text_widget.insert("end", "\n")  # Insert a newline after each line

    text_widget.config(state="disabled")  # Make it read-only

    # Update window width based on the table width
    text_width = (
        max(len(line) for line in table.split("\n")) * 7
    )  # Approximate character width
    window_width = text_width + 20  # Add extra padding of 10 on each side
    root.geometry(f"{window_width}x400")  # Set a fixed height for the window
