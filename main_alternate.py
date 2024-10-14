import os
from typing import Optional, List

import pandas as pd
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
from tkinter import ttk
from colorama import init
from tkinterdnd2 import DND_FILES, TkinterDnD
from ttkthemes import ThemedStyle

from app import log, time_function, CompatibleModel
from app.calculations import (
    compile_camera_mp_channels,
    get_camera_match,
)
from app.file_handling import parse_customer_list, parse_hardware_compatibility_list
from app.formatting import (
    get_manufacturer_set,
    sanitize_customer_data,
    list_verkada_camera_details,
)
from app.memory_management import MemoryStorage
from app.recommend import count_mp, recommend_connectors, calculate_4k_storage, calculate_low_mp_storage

# Initialize colorized output
init(autoreset=True)

# Constant strings
SELECT_CSV_TEXT = "Select CSV"
RUN_CHECK_TEXT = "Run Check"
ERROR_NO_FILE = "Error: No File Selected."
PROCESSING_TEXT = "Processing... Please Wait"
COMPLETED_TEXT = "Completed."
ERROR_PROCESSING = "Error: Could not process file."
DEFAULT_FILE_STATUS = "No File Selected."
DETAILS_LABEL = "Additional Details"

class CameraCompatibilityApp:
    def __init__(self, window):
        self.root = window
        self.change_detected_flag = True
        self.customer_file_path: Optional[str] = None
        self.file_status = StringVar(value=DEFAULT_FILE_STATUS)
        self.recommendation_enabled = IntVar(value=0)  # Variable for checkbox
        self.item_details = {}  # Store item details safely
        self.memory = MemoryStorage()  # Instantiate MemoryStorage
        self._setup_ui()
        self.toggle_recommendation_visibility()  # Set initial visibility

    def _setup_ui(self):
        self.root.title("Command Connector Compatibility Calculator")
        self.root.geometry("900x700")

        style = ThemedStyle(self.root)
        style.set_theme("equilux")
        style.configure(
            "RunButton.TButton", background="#fffcff", font=("Helvetica", 14, "bold")
        )

        self._create_widgets()
        self._setup_layout()
        self._configure_drag_and_drop()

    def _create_widgets(self):
        self.main_frame = ttk.Frame(self.root, padding="10")
        self.file_frame = self._create_file_frame()
        self.options_frame = self._create_options_frame()
        self.run_button = ttk.Button(
            self.main_frame,
            text=RUN_CHECK_TEXT,
            command=self.run_check,
            state="disabled",
            style="RunButton.TButton",
        )
        self.result_frame = self._create_result_frame()
        self.details_frame = self._create_details_frame()
        self.status_label = ttk.Label(
            self.main_frame, text="", font=("Helvetica", 14, "italic")
        )
        self.recommendation_frame = self._create_recommendation_frame()  # New frame for recommendations

    def _create_file_frame(self) -> Frame:
        file_frame = ttk.Frame(self.main_frame)
        ttk.Label(
            file_frame, textvariable=self.file_status, font=("Helvetica", 14)
        ).pack(side=LEFT, fill=X, expand=True)
        ttk.Button(file_frame, text=SELECT_CSV_TEXT, command=self.select_file).pack(
            side=RIGHT
        )
        return file_frame

    def _create_options_frame(self) -> Frame:
        options_frame = ttk.Frame(self.main_frame)

        # Frame for Retention Period input
        self.retention_frame = ttk.Frame(options_frame)
        self.retention_label = ttk.Label(
            self.retention_frame,
            text="Retention Period (days):",
            font=("Helvetica", 14),
        )
        self.retention_label.pack(side=LEFT, padx=(0, 10))
        self.retention = IntVar(value=30)
        self.retention_spinbox = ttk.Spinbox(
            self.retention_frame,
            from_=30,
            to=90,
            increment=30,
            textvariable=self.retention,
            width=5,
            command=self.change_detected,
        )
        self.retention_spinbox.pack(side=LEFT, padx=(0, 20))
        self.retention_frame.pack(side=LEFT)  # Initially packed, will be toggled

        # Checkbox for enabling recommendation
        self.recommendation_checkbox = ttk.Checkbutton(
            options_frame,
            text="Recommend Command Connectors",
            variable=self.recommendation_enabled,
            command=self.toggle_recommendation_visibility,
        )
        self.recommendation_checkbox.pack(side=LEFT)
        return options_frame

    def _create_result_frame(self) -> Frame:
        result_frame = ttk.Frame(self.main_frame)
        self.treeview = ttk.Treeview(
            result_frame,
            columns=("Name", "Count", "Matched Model"),
            show="headings",
        )
        for col in self.treeview["columns"]:
            self.treeview.heading(col, text=col)
        self.treeview.column("Name", width=250)
        self.treeview.column("Count", width=100, anchor="center")
        self.treeview.column("Matched Model", width=250)

        self.scrollbar_y = ttk.Scrollbar(
            result_frame, orient="vertical", command=self.treeview.yview
        )
        self.scrollbar_x = ttk.Scrollbar(
            result_frame, orient="horizontal", command=self.treeview.xview
        )
        self.treeview.configure(
            yscrollcommand=self.scrollbar_y.set, xscrollcommand=self.scrollbar_x.set
        )

        self.treeview.pack(side=LEFT, fill=BOTH, expand=True)
        self.scrollbar_y.pack(side=RIGHT, fill=Y)
        self.scrollbar_x.pack(side=BOTTOM, fill=X)
        return result_frame

    def _create_details_frame(self) -> Frame:
        details_frame = ttk.Frame(self.main_frame, padding="10")
        ttk.Label(details_frame, text=DETAILS_LABEL, font=("Helvetica", 14)).pack(
            anchor="w"
        )
        self.details_text = Text(
            details_frame, wrap=WORD, height=6, font=("Helvetica", 14)
        )
        self.details_text.config(state=DISABLED)
        self.details_text.pack(fill=BOTH, expand=True, pady=5)
        return details_frame

    def _create_recommendation_frame(self) -> Frame:
        recommendation_frame = ttk.Frame(self.main_frame, padding="10")
        ttk.Label(
            recommendation_frame,
            text="Command Connector Recommendations",
            font=("Helvetica", 14, "bold"),
        ).pack(anchor="w")

        self.recommendation_text = Text(
            recommendation_frame, wrap=WORD, height=4, font=("Helvetica", 14)
        )
        self.recommendation_text.config(state=DISABLED)
        self.recommendation_text.pack(fill=BOTH, expand=True, pady=5)
        return recommendation_frame

    def _setup_layout(self):
        self.main_frame.pack(fill=BOTH, expand=True)
        self.file_frame.pack(fill=X, pady=(0, 10))
        self.options_frame.pack(fill=X, pady=(0, 10))
        self.run_button.pack(fill=X, pady=(0, 10))
        self.result_frame.pack(fill=BOTH, expand=True)
        self.details_frame.pack(fill=X, pady=(10, 0))
        # self.recommendation_frame.pack(fill=X, pady=(10, 0))  # Initially not packed
        self.status_label.pack(fill=X, pady=(10, 0))

    def _configure_drag_and_drop(self):
        self.root.drop_target_register(DND_FILES)
        self.root.dnd_bind("<<Drop>>", self.on_drop)

    def on_drop(self, event):
        self.change_detected()
        self._update_file_selection(event.data.strip("{}"))

    def select_file(self):
        self.change_detected()
        file_path = filedialog.askopenfilename(filetypes=[("CSV files", "*.csv")])
        if file_path:
            self._update_file_selection(file_path)

    def _update_file_selection(self, file_selection: str):
        self.customer_file_path = file_selection
        self.file_status.set(f"Selected: {os.path.basename(self.customer_file_path)}")
        self.run_button.config(state="normal", style="RunButton.TButton")
        self.status_label.config(
            text="File loaded. Click 'Run Check' to process.",
            foreground="#ccffcc",
            font=("Helvetica", 14),
        )

    @time_function
    def run_check(self):
        if not self.customer_file_path:
            self.status_label.config(
                text=ERROR_NO_FILE, foreground="#ffcccc", font=("Helvetica", 14)
            )
            return

        self.status_label.config(
            text=PROCESSING_TEXT, foreground="#fff2cc", font=("Helvetica", 14)
        )
        self.root.update()

        try:
            # Allow user to select compatibility list file if needed
            compatibility_file = "Verkada Command Connector Compatibility.csv"
            if not os.path.exists(compatibility_file):
                compatibility_file = filedialog.askopenfilename(
                    title="Select Compatibility List CSV",
                    filetypes=[("CSV files", "*.csv")],
                )
                if not compatibility_file:
                    self.status_label.config(
                        text="Error: Compatibility list not found.",
                        foreground="#ffcccc",
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
                self._display_results(matched_cameras, verkada_compatibility_list)
                self.status_label.config(
                    text=COMPLETED_TEXT, foreground="#ccffcc", font=("Helvetica", 14)
                )

                # If recommendation is enabled, perform recommendations
                if self.recommendation_enabled.get():
                    self._perform_recommendations(matched_cameras, verkada_compatibility_list)
                else:
                    self.recommendation_text.config(state=NORMAL)
                    self.recommendation_text.delete(1.0, END)
                    self.recommendation_text.insert(END, "Recommendations not enabled.")
                    self.recommendation_text.config(state=DISABLED)
            else:
                self.status_label.config(
                    text=ERROR_PROCESSING, foreground="#ffcccc", font=("Helvetica", 14)
                )
        except Exception as e:
            log.error("Error in run_check: %s", str(e))
            self.status_label.config(
                text=f"Error: {str(e)}", foreground="#ffcccc", font=("Helvetica", 14)
            )
        self.toggle_change()

    def _display_results(
        self, matched_cameras: pd.DataFrame, verkada_list: List[CompatibleModel]
    ):
        self.treeview.delete(*self.treeview.get_children())
        self._configure_tags()

        for _, row in matched_cameras.iterrows():
            verkada_details = list_verkada_camera_details(
                row["verkada_model"], verkada_list
            )
            details = {
                "Match Type": row["match_type"],
                "Manufacturer": verkada_details[1]
                if pd.notna(verkada_details[1])
                else "N/A",
                "Min. Firmware": verkada_details[2]
                if pd.notna(verkada_details[2])
                else "N/A",
                "Notes": verkada_details[3] if pd.notna(verkada_details[3]) else "N/A",
            }

            match_type = row.get("match_type", "unknown").lower()
            tag = self._get_tag_for_match_type(str(match_type))

            item_id = self.treeview.insert(
                "",
                "end",
                values=(row["name"], int(row["count"]), row["verkada_model"]),
                tags=(tag,),
            )
            self.item_details[item_id] = details

        self.treeview.bind("<ButtonRelease-1>", self.on_tree_click)

    def _configure_tags(self):
        # Configure tags for different match types with softer colors
        self.treeview.tag_configure("unsupported", foreground="#ff4d4d")
        self.treeview.tag_configure("potential", foreground="#ffcc00")
        self.treeview.tag_configure("exact", foreground="#33cc33")
        self.treeview.tag_configure("identified", foreground="#3399ff")

    def _get_tag_for_match_type(self, match_type: str) -> Optional[str]:
        tag_map = {
            "unsupported": "unsupported",
            "potential": "potential",
            "exact": "exact",
            "identified": "identified",
        }
        return tag_map.get(match_type, None)

    def on_tree_click(self, event):
        item = self.treeview.identify_row(event.y)
        if item:
            details = self.item_details.get(item)
            if details:
                self.display_details(details)

    def display_details(self, details):
        self.details_text.config(state=NORMAL)
        self.details_text.delete(1.0, END)

        details_text = "\n".join(f"{key}: {value}" for key, value in details.items())

        self.details_text.insert(END, details_text)
        self.details_text.config(state=DISABLED)

    def _perform_recommendations(
        self, matched_cameras: pd.DataFrame, verkada_list: List[CompatibleModel]
    ):
        # Count the number of low and high MP cameras
        low_mp_count, high_mp_count = count_mp(matched_cameras, verkada_list)
        retention_days = self.retention.get()

        # Calculate storage requirements
        low_storage = calculate_low_mp_storage(low_mp_count, retention_days)
        high_storage = calculate_4k_storage(high_mp_count, retention_days)
        total_storage = low_storage + high_storage

        # Call the recommend_connectors function
        recommend_connectors(
            change=True,
            retention=retention_days,
            camera_dataframe=matched_cameras,
            verkada_camera_list=verkada_list,
            memory=self.memory,
        )

        # Retrieve recommendations and excess channels
        recommendations = self.memory.get_recommendations()
        excess_channels = self.memory.get_excess_channels()

        # Display the recommendations
        self.recommendation_text.config(state=NORMAL)
        self.recommendation_text.delete(1.0, END)

        if recommendations:
            rec_text = "Recommended Command Connectors:\n"
            rec_text += "\n".join([conn["name"] for conn in recommendations])
            rec_text += f"\n\nExcess Channels: {excess_channels}"
            self.recommendation_text.insert(END, rec_text)
        else:
            self.recommendation_text.insert(END, "No recommendations available.")

        self.recommendation_text.config(state=DISABLED)

    def toggle_recommendation_visibility(self):
        if self.recommendation_enabled.get():
            self.retention_frame.pack(side=LEFT)
            self.recommendation_frame.pack(fill=X, pady=(10, 0))
        else:
            self.retention_frame.pack_forget()
            self.recommendation_frame.pack_forget()
        self.change_detected()

    def toggle_change(self):
        log.debug(
            "Setting self.change_detected_flag from %s to %s.",
            self.change_detected_flag,
            not self.change_detected_flag,
        )
        self.change_detected_flag = not self.change_detected_flag

    def change_detected(self):
        log.debug("Change detected")
        self.change_detected_flag = True
        self.status_label.config(
            text="Changes detected. Re-run the check for updated results.",
            foreground="#cce5ff",
        )


if __name__ == "__main__":
    root = TkinterDnD.Tk()
    app = CameraCompatibilityApp(root)
    root.mainloop()