"""
Author: Mehul Sen
Co-Author: Ian Young
Purpose: Import a list of third-party cameras and return
    which cameras are compatible with the cloud connector.
"""

import os
from typing import Optional, List

from tkinter import (
    Frame,
    Text,
    filedialog,
    IntVar,
    StringVar,
    BOTH,
    LEFT,
    RIGHT,
    BOTTOM,
    X,
    Y,
    WORD,
    END,
    DISABLED,
    NORMAL,
)
from tkinter import ttk, TclError
import pandas as pd
from colorama import init
from tkinterdnd2 import DND_FILES, TkinterDnD

from app import log, time_function, CompatibleModel
from app.calculations import (
    compile_camera_mp_channels,
    get_camera_match,
)
from app.file_handling import (
    parse_customer_list,
    parse_hardware_compatibility_list,
)
from app.formatting import (
    get_manufacturer_set,
    sanitize_customer_data,
    list_verkada_camera_details,
    export_to_csv,
)
from app.memory_management import MemoryStorage
from app.recommend import recommend_connectors

init(autoreset=True)

SELECT_CSV_TEXT = "Select CSV"
RUN_CHECK_TEXT = "Run Check"
EXPORT_TEXT = "Export CSV"
ERROR_NO_FILE = "Error: No File Selected"
PROCESSING_TEXT = "Processing... Please Wait"
COMPLETED_TEXT = "Completed"
ERROR_PROCESSING = "Error: Could not process File"
DEFAULT_FILE_STATUS = "No File Selected"
DETAILS_LABEL = "Additional Details"
GREEN_COLOR = "#a0e77d"
YELLOW_COLOR = "#ebd671"
RED_COLOR = "#ef8677"
BLUE_COLOR = "#82b6d9"


class CameraCompatibilityApp:
    """A class to manage the GUI for Command Connector Compatibility Calculator."""

    def __init__(self, window):
        """Initializes the Camera Compatibility class."""
        self.root = window
        self.change_detected_flag = True
        self.customer_file_path: Optional[str] = None
        self.memory = MemoryStorage()

        # Retention spinbox value
        self.retention = IntVar(value=30)
        self.recommendation_enabled = IntVar(value=0)

        # UI elements stored in one dictionary
        self.ui_elements = {
            "file_status": StringVar(value=DEFAULT_FILE_STATUS),
            "treeview": None,
            "item_details": {},
        }

        # Set up the user interface
        self._setup_ui()
        self.toggle_recommendation_visibility()

    def _setup_ui(self):
        """Sets up the main UI elements for the application."""
        self.root.title("Command Connector Compatibility Calculator")
        self.root.geometry("1000x1000")

        style = ttk.Style(self.root)
        # clam, alt, default, classic
        style.theme_use("clam")
        style.configure(
            "RunButton.TButton",
            font=("Helvetica", 14, "bold"),
        )

        self._create_widgets()
        self._setup_layout()
        self._configure_drag_and_drop()

    def _create_widgets(self):
        """Creates the widgets (buttons, labels, frames) for the UI."""
        self.ui_elements["main_frame"] = ttk.Frame(self.root, padding="10")
        self.ui_elements["file_frame"] = self._create_file_frame()
        self.ui_elements["options_frame"] = self._create_options_frame()
        self.ui_elements["run_button"] = ttk.Button(
            self.ui_elements["main_frame"],
            text=RUN_CHECK_TEXT,
            command=self.run_check,
            state="disabled",
            style="RunButton.TButton",
        )
        self.ui_elements["status_label"] = ttk.Label(
            self.ui_elements["main_frame"],
            text="",
            font=("Helvetica", 14, "italic"),
        )
        self.ui_elements["result_frame"] = self._create_result_frame()
        self.ui_elements["details_frame"] = self._create_details_frame()
        self.ui_elements["recommendation_frame"] = (
            self._create_recommendation_frame()
        )

    def _create_file_frame(self) -> Frame:
        """Creates the file selection frame."""
        file_frame = ttk.Frame(self.ui_elements["main_frame"])
        ttk.Label(
            file_frame,
            textvariable=self.ui_elements["file_status"],
            font=("Helvetica", 14),
        ).pack(side=LEFT, fill=X, expand=True)
        ttk.Button(
            file_frame, text=SELECT_CSV_TEXT, command=self.select_file
        ).pack(side=LEFT)
        self.ui_elements["export_button"] = ttk.Button(
            file_frame,
            text=EXPORT_TEXT,
            command=self.export_results,
            state="disabled",
            style="Export.TButton",
        )
        self.ui_elements["export_button"].pack(side=RIGHT)
        return file_frame

    def _create_options_frame(self) -> Frame:
        """Creates the options frame."""
        options_frame = ttk.Frame(self.ui_elements["main_frame"])

        # Frame for retention period input
        self.ui_elements["retention_frame"] = ttk.Frame(options_frame)
        ttk.Label(
            self.ui_elements["retention_frame"],
            text="Retention Period (days):",
            font=("Helvetica", 14),
        ).pack(side=LEFT, padx=(10, 10))
        retention_spinbox = ttk.Spinbox(
            self.ui_elements["retention_frame"],
            from_=30,
            to=90,
            increment=30,
            textvariable=self.retention,
            width=5,
            command=self.change_detected,
        )
        retention_spinbox.pack(side=LEFT, padx=(0, 20))
        self.ui_elements["retention_frame"].pack(side=LEFT)

        # Checkbox to enable/disable recommendations
        self.ui_elements["recommendation_checkbox"] = ttk.Checkbutton(
            options_frame,
            text="Recommend CCs",
            variable=self.recommendation_enabled,
            command=self.toggle_recommendation_visibility,
        )
        self.ui_elements["recommendation_checkbox"].pack(side=LEFT)
        return options_frame

    def _create_result_frame(self) -> Frame:
        """Creates the frame to display the results (matched cameras)."""
        result_frame = ttk.Frame(self.ui_elements["main_frame"])

        # Store columns in a variable
        columns = ("Name", "Count", "Matched Model")
        self.ui_elements["treeview"] = ttk.Treeview(
            result_frame,
            columns=columns,
            show="headings",
        )

        # Use the columns variable instead of subscripting the treeview
        for col in columns:
            self.ui_elements["treeview"].heading(col, text=col)
        self.ui_elements["treeview"].column("Name", width=250)
        self.ui_elements["treeview"].column(
            "Count", width=100, anchor="center"
        )
        self.ui_elements["treeview"].column("Matched Model", width=250)

        scrollbar_y = ttk.Scrollbar(
            result_frame,
            orient="vertical",
            command=self.ui_elements["treeview"].yview,
        )
        scrollbar_x = ttk.Scrollbar(
            result_frame,
            orient="horizontal",
            command=self.ui_elements["treeview"].xview,
        )
        self.ui_elements["treeview"].configure(
            yscrollcommand=scrollbar_y.set,
            xscrollcommand=scrollbar_x.set,
        )

        self.ui_elements["treeview"].pack(side=LEFT, fill=BOTH, expand=True)
        scrollbar_y.pack(side=RIGHT, fill=Y)
        scrollbar_x.pack(side=BOTTOM, fill=X)
        return result_frame

    def _create_details_frame(self) -> Frame:
        """Creates the details frame to display additional information about the selected camera."""
        details_frame = ttk.Frame(self.ui_elements["main_frame"], padding="10")
        ttk.Label(
            details_frame, text=DETAILS_LABEL, font=("Helvetica", 14)
        ).pack(anchor="w")
        self.ui_elements["details_text"] = Text(
            details_frame, wrap=WORD, height=6, font=("Helvetica", 14)
        )
        self.ui_elements["details_text"].config(state=DISABLED)
        self.ui_elements["details_text"].pack(fill=BOTH, expand=True, pady=5)
        return details_frame

    def _create_recommendation_frame(self) -> Frame:
        """Creates the frame to display recommendations for connectors."""
        recommendation_frame = ttk.Frame(
            self.ui_elements["main_frame"], padding="10"
        )
        ttk.Label(
            recommendation_frame,
            text="Command Connector Recommendations",
            font=("Helvetica", 14),
        ).pack(anchor="w")

        self.ui_elements["recommendation_text"] = Text(
            recommendation_frame, wrap=WORD, height=4, font=("Helvetica", 14)
        )
        self.ui_elements["recommendation_text"].config(state=DISABLED)
        self.ui_elements["recommendation_text"].pack(
            fill=BOTH, expand=True, pady=5
        )
        return recommendation_frame

    def _setup_layout(self):
        """Arranges the layout of the main UI frames."""
        self.ui_elements["main_frame"].pack(fill=BOTH, expand=True)
        self.ui_elements["file_frame"].pack(fill=X, pady=(0, 10))
        self.ui_elements["options_frame"].pack(fill=X, pady=(0, 10))
        self.ui_elements["run_button"].pack(fill=X, pady=(0, 10))
        self.ui_elements["status_label"].pack(fill=X, pady=(10, 0))
        self.ui_elements["result_frame"].pack(fill=BOTH, expand=True)
        self.ui_elements["details_frame"].pack(fill=X, pady=(10, 0))

    def _configure_drag_and_drop(self):
        """Configures drag-and-drop functionality for file selection."""
        self.root.drop_target_register(DND_FILES)
        self.root.dnd_bind("<<Drop>>", self.on_drop)

    def on_drop(self, event):
        """Handles file drop events."""
        self.change_detected()
        self._update_file_selection(event.data.strip("{}"))

    def select_file(self):
        """Opens a file dialog for selecting a customer CSV file."""
        self.change_detected()
        if file_path := filedialog.askopenfilename(
            filetypes=[("CSV files", "*.csv")]
        ):
            self._update_file_selection(file_path)

    def _update_file_selection(self, file_selection: str):
        """Updates the file selection label and enables the run button."""
        self.customer_file_path = file_selection
        file_name = os.path.basename(self.customer_file_path)
        self.ui_elements["file_status"].set(f"Selected: {file_name}")
        self.ui_elements["run_button"].config(
            state="normal", style="RunButton.TButton"
        )
        self.ui_elements["status_label"].config(
            text="File loaded. Click 'Run Check' to process.",
            foreground="#0e4503",
            font=("Helvetica", 14),
        )

    @time_function
    def export_results(self):
        """Exports results to a CSV file."""
        cameras_dataframe = self.memory.get_results()
        files = [("CSV files", "*.csv"), ("All Files", "*.*")]
        filepath = filedialog.asksaveasfilename(filetypes=files)
        export_to_csv(cameras_dataframe, filepath)

    @time_function
    def run_check(self):
        """Runs the compatibility check when the 'Run Check' button is clicked."""
        if not self.customer_file_path:
            self.ui_elements["status_label"].config(
                text=ERROR_NO_FILE,
                foreground="#6b0601",
                font=("Helvetica", 14),
            )
            return

        self.ui_elements["status_label"].config(
            text=PROCESSING_TEXT, foreground="#8f6400", font=("Helvetica", 14)
        )
        self.root.update()

        try:
            compatibility_file = "Verkada Command Connector Compatibility.csv"
            if not os.path.exists(compatibility_file):
                compatibility_file = filedialog.askopenfilename(
                    title="Select Compatibility List CSV",
                    filetypes=[("CSV files", "*.csv")],
                )
                if not compatibility_file:
                    self.ui_elements["status_label"].config(
                        text="Error: Compatibility list not found.",
                        foreground="#6b0601",
                        font=("Helvetica", 14),
                    )
                    return

            verkada_compatibility_list = compile_camera_mp_channels(
                parse_hardware_compatibility_list(compatibility_file)
            )
            customer_cameras_list = sanitize_customer_data(
                parse_customer_list(self.customer_file_path),
                get_manufacturer_set(verkada_compatibility_list),
            )
            matched_cameras = get_camera_match(
                customer_cameras_list, verkada_compatibility_list
            )

            if matched_cameras is not None:

                self.memory.set_results(matched_cameras)
                self.ui_elements["export_button"].config(
                    state="normal", style="Export.TButton"
                )

                self._display_results(
                    matched_cameras, verkada_compatibility_list
                )
                self.ui_elements["status_label"].config(
                    text=COMPLETED_TEXT,
                    foreground="#0e4503",
                    font=("Helvetica", 14),
                )

                if self.recommendation_enabled.get():
                    self._perform_recommendations(
                        matched_cameras, verkada_compatibility_list
                    )
                else:
                    self.ui_elements["recommendation_text"].config(
                        state=NORMAL
                    )
                    self.ui_elements["recommendation_text"].delete(1.0, END)
                    self.ui_elements["recommendation_text"].insert(
                        END, "Recommendations not enabled."
                    )
                    self.ui_elements["recommendation_text"].config(
                        state=DISABLED
                    )
            else:
                self.ui_elements["status_label"].config(
                    text=ERROR_PROCESSING,
                    foreground="#6b0601",
                    font=("Helvetica", 14),
                )
        except FileNotFoundError as e:
            log.error("File not found: %s", str(e))
            self.ui_elements["status_label"].config(
                text="Error: File not found.",
                foreground="#6b0601",
                font=("Helvetica", 14),
            )
        except pd.errors.EmptyDataError as e:
            log.error("Error in run_check: Empty CSV file. %s", str(e))
            self.ui_elements["status_label"].config(
                text="Error: Empty CSV file.",
                foreground="#6b0601",
                font=("Helvetica", 14),
            )
        self.toggle_change()

    def _display_results(
        self,
        matched_cameras: pd.DataFrame,
        verkada_list: List[CompatibleModel],
    ):
        """Displays the matched cameras in the Treeview widget."""
        self.ui_elements["treeview"].delete(
            *self.ui_elements["treeview"].get_children()
        )
        self._configure_tags()

        for _, row in matched_cameras.iterrows():
            verkada_details = list_verkada_camera_details(
                row["verkada_model"], verkada_list
            )
            details = {
                "Match Type": row["match_type"],
                "Manufacturer": (
                    verkada_details[1]
                    if pd.notna(verkada_details[1])
                    else "N/A"
                ),
                "Min. Firmware": (
                    verkada_details[2]
                    if pd.notna(verkada_details[2])
                    else "N/A"
                ),
                "Notes": (
                    verkada_details[3]
                    if pd.notna(verkada_details[3])
                    else "N/A"
                ),
            }

            match_type = row.get("match_type", "unknown").lower()
            tag = self._get_tag_for_match_type(str(match_type))

            item_id = self.ui_elements["treeview"].insert(
                "",
                "end",
                values=(row["name"], int(row["count"]), row["verkada_model"]),
                tags=(tag,),
            )
            self.ui_elements["item_details"][item_id] = details

        self.ui_elements["treeview"].bind(
            "<ButtonRelease-1>", self.on_tree_click
        )

    def _configure_tags(self):
        """Configures tags to color-code the Treeview rows based on match type."""
        self.ui_elements["treeview"].tag_configure(
            "unsupported", foreground="#000000", background=RED_COLOR
        )
        self.ui_elements["treeview"].tag_configure(
            "potential", foreground="#000000", background=YELLOW_COLOR
        )
        self.ui_elements["treeview"].tag_configure(
            "exact", foreground="#000000", background=GREEN_COLOR
        )
        self.ui_elements["treeview"].tag_configure(
            "identified", foreground="#000000", background=BLUE_COLOR
        )

    def _get_tag_for_match_type(self, match_type: str) -> Optional[str]:
        """Returns the appropriate tag for a given match type."""
        tag_map = {
            "unsupported": "unsupported",
            "potential": "potential",
            "exact": "exact",
            "identified": "identified",
        }
        return tag_map.get(match_type)

    def on_tree_click(self, event):
        """Handles clicks on the Treeview rows to display additional camera details."""
        if item := self.ui_elements["treeview"].identify_row(event.y):
            if details := self.ui_elements["item_details"].get(item):
                self.display_details(details)

    def display_details(self, details):
        """Displays the details of the selected camera in the details text box."""
        self.ui_elements["details_text"].config(state=NORMAL)
        self.ui_elements["details_text"].delete(1.0, END)

        details_text = "\n".join(
            f"{key}: {value}" for key, value in details.items()
        )

        self.ui_elements["details_text"].insert(END, details_text)
        self.ui_elements["details_text"].config(state=DISABLED)

    def _perform_recommendations(
        self,
        matched_cameras: pd.DataFrame,
        verkada_list: List[CompatibleModel],
    ):
        """Performs the recommendation of connectors based on cameras and retention period."""
        retention_days = self.retention.get()

        recommend_connectors(
            change=True,
            retention=retention_days,
            camera_dataframe=matched_cameras,
            verkada_camera_list=verkada_list,
            memory=self.memory,
        )

        recommendations = self.memory.get_recommendations()
        excess_channels = self.memory.get_excess_channels()

        self.ui_elements["recommendation_text"].config(state=NORMAL)
        self.ui_elements["recommendation_text"].delete(1.0, END)

        if recommendations:
            rec_text = "Recommended Command Connectors:\n" + "\n".join(
                [conn["name"] for conn in recommendations]
            )
            rec_text += f"\n\nExcess Channels: {excess_channels}"
            self.ui_elements["recommendation_text"].insert(END, rec_text)
        else:
            self.ui_elements["recommendation_text"].insert(
                END, "No recommendations available."
            )

        self.ui_elements["recommendation_text"].config(state=DISABLED)

    def toggle_recommendation_visibility(self):
        """Toggles the visibility of the recommendation UI elements based on the checkbox state."""
        if self.recommendation_enabled.get():
            self.ui_elements["retention_frame"].pack(side=LEFT)
            self.ui_elements["recommendation_frame"].pack(fill=X, pady=(10, 0))
        else:
            self.ui_elements["retention_frame"].pack_forget()
            self.ui_elements["recommendation_frame"].pack_forget()

    def toggle_change(self):
        """Toggles the change detection flag."""
        log.debug(
            "Setting self.change_detected_flag from %s to %s.",
            self.change_detected_flag,
            not self.change_detected_flag,
        )
        self.change_detected_flag = not self.change_detected_flag

    def change_detected(self):
        """Handles change detection and updates the status label accordingly."""
        log.debug("Change detected")
        self.change_detected_flag = True
        self.ui_elements["status_label"].config(
            text="Changes detected. Re-run the check for updated results.",
            foreground="#004c8f",
        )


if __name__ == "__main__":
    try:
        root = TkinterDnD.Tk()
        app = CameraCompatibilityApp(root)
        root.mainloop()
    except TclError:
        print("Exiting. No display detected.")
