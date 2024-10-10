"""
Author: Ian Young
Co-Author: Mehul Sen
Purpose: Create a GUI through which the application may be run and managed.
"""

import os
import ast
from subprocess import check_call
from sys import executable
from typing import Optional, List

import pandas as pd
from tkinter import (
    Button,
    Frame,
    Label,
    Scrollbar,
    Text,
    filedialog,
    Spinbox,
    IntVar,
    StringVar,
    BOTH,
    LEFT,
    RIGHT,
    BOTTOM,
    X,
    Y,
    ttk, WORD, END, DISABLED,
)
from colorama import Fore, Style, init
from tkinterdnd2 import DND_FILES, TkinterDnD
from ttkthemes import ThemedStyle

from app import log, time_function, CompatibleModel
from app.calculations import compile_camera_mp_channels, get_camera_match
from app.memory_management import MemoryStorage
from app.file_handling import parse_customer_list, parse_hardware_compatibility_list
from app.formatting import get_manufacturer_set, sanitize_customer_data, list_verkada_camera_details

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
        self.memory = MemoryStorage()
        self.change_detected_flag = True
        self.customer_file_path: Optional[str] = None
        self.file_status = StringVar(value=DEFAULT_FILE_STATUS)
        self._setup_ui()

    def _setup_ui(self):
        self.root.title("Command Connector Compatibility Calculator")
        self.root.geometry("800x600")

        style = ThemedStyle(self.root)
        style.set_theme("equilux")
        style.configure("RunButton.TButton", background="#ffffff", font=("Helvetica", 14, "bold"))

        self._create_widgets()
        self._setup_layout()
        self._configure_drag_and_drop()

    def _create_widgets(self):
        self.main_frame = ttk.Frame(self.root, padding="10")
        self.file_frame = self._create_file_frame()
        self.options_frame = self._create_options_frame()
        self.run_button = ttk.Button(self.main_frame, text=RUN_CHECK_TEXT, command=self.run_check, state="disabled", style="RunButton.TButton")
        self.result_frame = self._create_result_frame()
        self.details_frame = self._create_details_frame()
        self.status_label = ttk.Label(self.main_frame, text="", font=("Helvetica", 14, "italic"))

    def _create_file_frame(self) -> Frame:
        file_frame = ttk.Frame(self.main_frame)
        ttk.Label(file_frame, textvariable=self.file_status, font=("Helvetica", 14)).pack(side=LEFT, fill=X, expand=True)
        ttk.Button(file_frame, text=SELECT_CSV_TEXT, command=self.select_file).pack(side=RIGHT)
        return file_frame

    def _create_options_frame(self) -> Frame:
        options_frame = ttk.Frame(self.main_frame)
        ttk.Label(options_frame, text="Retention Period (days):", font=("Helvetica", 14)).pack(side=LEFT, padx=(0, 10))
        self.retention = IntVar(value=30)
        ttk.Spinbox(
            options_frame,
            from_=30,
            to=90,
            increment=30,
            textvariable=self.retention,
            width=5,
            command=self.change_detected
        ).pack(side=LEFT)
        return options_frame

    def _create_result_frame(self) -> Frame:
        result_frame = ttk.Frame(self.main_frame)
        self.text_widget = ttk.Treeview(result_frame, columns=("Name", "Count", "Matched Model"), show="headings")
        for col in self.text_widget["columns"]:
            self.text_widget.heading(col, text=col)
        self.text_widget.column("Name", width=150)
        self.text_widget.column("Count", width=50, anchor="center")
        self.text_widget.column("Matched Model", width=150)

        self.scrollbar_y = ttk.Scrollbar(result_frame, orient="vertical", command=self.text_widget.yview)
        self.scrollbar_x = ttk.Scrollbar(result_frame, orient="horizontal", command=self.text_widget.xview)
        self.text_widget.configure(yscrollcommand=self.scrollbar_y.set, xscrollcommand=self.scrollbar_x.set)

        self.text_widget.pack(side=LEFT, fill=BOTH, expand=True)
        self.scrollbar_y.pack(side=RIGHT, fill=Y)
        self.scrollbar_x.pack(side=BOTTOM, fill=X)
        return result_frame

    def _create_details_frame(self) -> Frame:
        details_frame = ttk.Frame(self.main_frame, padding="10")
        ttk.Label(details_frame, text=DETAILS_LABEL, font=("Helvetica", 14)).pack(anchor="w")
        self.details_text = Text(details_frame, wrap=WORD, height=4, font=("Helvetica", 14))
        self.details_text.config(state=DISABLED)
        self.details_text.pack(fill=BOTH, expand=True, pady=5)
        return details_frame

    def _setup_layout(self):
        self.main_frame.pack(fill=BOTH, expand=True)
        self.file_frame.pack(fill=X, pady=(0, 10))
        self.options_frame.pack(fill=X, pady=(0, 10))
        self.run_button.pack(fill=X, pady=(0, 10))
        self.result_frame.pack(fill=BOTH, expand=True)
        self.details_frame.pack(fill=X, pady=(10, 0))
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
        self.run_button.config(state="normal")
        self.status_label.config(text="File loaded. Click 'Run Check' to process.", foreground="#ccffcc", font=("Helvetica", 14))

    @time_function
    def run_check(self):
        if not self.customer_file_path:
            self.status_label.config(text=ERROR_NO_FILE, foreground="#ffcccc", font=("Helvetica", 14))
            return

        self.status_label.config(text=PROCESSING_TEXT, foreground="#fff2cc", font=("Helvetica", 14))
        self.root.update()

        try:
            verkada_compatibility_list = compile_camera_mp_channels(
                parse_hardware_compatibility_list("Verkada Command Connector Compatibility.csv")
            )
            customer_cameras_list = sanitize_customer_data(
                parse_customer_list(self.customer_file_path),
                get_manufacturer_set(verkada_compatibility_list),
            )
            matched_cameras = get_camera_match(customer_cameras_list, verkada_compatibility_list)

            if matched_cameras is not None:
                self._display_results(matched_cameras, verkada_compatibility_list)
                self.status_label.config(text=COMPLETED_TEXT, foreground="#ccffcc", font=("Helvetica", 14))
            else:
                self.status_label.config(text=ERROR_PROCESSING, foreground="#ffcccc", font=("Helvetica", 14))
        except Exception as e:
            self.status_label.config(text=f"Error: {str(e)}", foreground="#ffcccc", font=("Helvetica", 14))
        self.toggle_change()

    def _display_results(self, matched_cameras: pd.DataFrame, verkada_list: List[CompatibleModel]):
        self.text_widget.delete(*self.text_widget.get_children())
        self._configure_tags()

        for index, row in matched_cameras.iterrows():
            verkada_details = list_verkada_camera_details(row["verkada_model"], verkada_list)
            details = {
                "match_type": row["match_type"],
                "manufacturer": verkada_details[1] if pd.notna(verkada_details[1]) else "N/A",
                "firmware": verkada_details[2] if pd.notna(verkada_details[2]) else "N/A",
                "notes": verkada_details[3] if pd.notna(verkada_details[3]) else "N/A"
            }

            match_type = row.get("match_type", "unknown").lower()
            tag = self._get_tag_for_match_type(match_type)

            self.text_widget.insert("", "end", values=(row["name"], int(row["count"]), row["verkada_model"]), tags=(str(details), tag))

        self.text_widget.bind("<ButtonRelease-1>", self.on_tree_click)

    def _configure_tags(self):
        # Configure tags for different match types with softer colors
        self.text_widget.tag_configure('unsupported', background='#ffcccc', foreground='#660000')
        self.text_widget.tag_configure('potential', background='#fff2cc', foreground='#665500')
        self.text_widget.tag_configure('exact', background='#ccffcc', foreground='#006600')
        self.text_widget.tag_configure('identified', background='#cce5ff', foreground='#003366')

    def _get_tag_for_match_type(self, match_type: str) -> Optional[str]:
        tag_map = {
            "unsupported": 'unsupported',
            "potential": 'potential',
            "exact": 'exact',
            "identified": 'identified',
        }
        return tag_map.get(match_type, None)

    def on_tree_click(self, event):
        item = self.text_widget.identify_row(event.y)
        if item:
            details_str = self.text_widget.item(item, 'tags')[0]
            try:
                details = ast.literal_eval(details_str)
                self.display_details(details)
            except (SyntaxError, ValueError):
                log.error("Error parsing details: %s", details_str)

    def display_details(self, details):
        self.details_text.config(state="normal")
        self.details_text.delete(1.0, END)

        details_text = (
            f"Match Type: {details.get('match_type')}\n"
            f"Manufacturer: {details.get('manufacturer')}\n"
            f"Min. Firmware: {details.get('firmware')}\n"
            f"Notes: {details.get('notes')}"
        )
        print(details_text)

        self.details_text.insert(END, details_text)
        self.details_text.config(state=DISABLED)

    def toggle_change(self):
        log.debug("Setting self.change from %s to %s.", self.change_detected_flag, not self.change_detected_flag)
        self.change_detected_flag = not self.change_detected_flag

    def change_detected(self):
        log.debug("Change detected")
        self.change_detected_flag = True
        self.status_label.config(text="Changes detected. Re-run the check for updated results.", foreground="blue")


if __name__ == "__main__":
    root = TkinterDnD.Tk()
    app = CameraCompatibilityApp(root)
    root.mainloop()
