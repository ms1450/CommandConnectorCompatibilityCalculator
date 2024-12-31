"""
Author: Mehul Sen
Co-Author: Ian Young
Purpose: Import a list of third-party cameras and return
    which cameras are compatible with the command connector.
"""
# Standard library imports
import os
from typing import List
from tkinter import filedialog

# Third-party imports
import customtkinter as ctk
import pandas

# Local imports
from app.calculations import compile_camera_mp_channels, get_camera_match
from app.file_handling import (
    parse_hardware_compatibility_list,
    parse_customer_list,
)
from app.formatting import (
    list_verkada_camera_details,
    export_to_csv,
)
from app.memory_management import MemoryStorage
from app.recommend import recommend_connectors

ctk.set_appearance_mode("System")
ctk.set_default_color_theme("blue")

class App(ctk.CTk):
    """A class to manage the GUI for Command Connector Compatibility Calculator."""
    def __init__(self):
        """Initialize the application and its components."""
        super().__init__()

        # Initialize all attributes in __init__
        self.file_paths: List[str] = []
        self.command_connector_compatibility_list = (
            "Verkada Command Connector Compatibility.csv"
        )
        self.verkada_compatibility_list = None
        self.current_camera_list = None
        self.recommend_cc_value = 0
        self.force_column_value = 0

        # Initialize UI components
        self.sidebar_frame = None
        self.logo_label = None
        self.tabview = None
        self.select_button = None
        self.scrollable_frame = None
        self.force_column_entry = None
        self.main_frame = None
        self.top_frame = None
        self.page_label = None
        self.export_button = None
        self.bottom_frame = None
        self.output_scrollable = None
        self.info_panel = None
        self.general_info_label = None
        self.general_info_frame = None
        self.camera_details_label = None
        self.camera_details_frame = None
        self.current_file_info = {}

        # Setup initial window configuration
        self.title("Command Connector Compatibility Calculator")
        self.geometry(f"{1100}x{580}")
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # Load compatibility list
        self.verkada_compatibility_list = compile_camera_mp_channels(
            parse_hardware_compatibility_list(
                self.command_connector_compatibility_list
            )
        )

        # Initialize UI components
        self._init_sidebar()
        self._create_main_window()

    def _init_sidebar(self):
        self.sidebar_frame = ctk.CTkFrame(
            self, width=300, corner_radius=0
        )
        self.sidebar_frame.grid(row=0, column=0, sticky="nsew")
        self.sidebar_frame.grid_propagate(False)
        self.sidebar_frame.grid_columnconfigure(0, weight=1)
        self.sidebar_frame.grid_rowconfigure(1, weight=1)

        self.logo_label = ctk.CTkLabel(
            self.sidebar_frame,
            text="Command Connector\nCompatibility Calculator",
            font=ctk.CTkFont(size=20, weight="bold"),
            justify="center",
            wraplength=300,
        )
        self.logo_label.grid(row=0, column=0, padx=5, pady=5, sticky="nsew")

        self.tabview = ctk.CTkTabview(
            self.sidebar_frame, width=260
        )
        self.tabview.grid(row=1, column=0, padx=5, pady=5, sticky="nsew")
        self.tabview.add("Basic")
        self.tabview.add("Settings")

        for tab_name in ["Basic", "Settings"]:
            self.tabview.tab(tab_name).grid_columnconfigure(0, weight=1)
            self.tabview.tab(tab_name).grid_rowconfigure(1, weight=1)

        self._setup_basic_tab()
        self._setup_settings_tab()

    def _setup_basic_tab(self):
        self.select_button = ctk.CTkButton(
            self.tabview.tab("Basic"),
            text="Import File(s)",
            command=self.select_files_event,
            height=32,
        )
        self.select_button.grid(row=0, column=0, sticky="ew", pady=5, padx=5)

        self.scrollable_frame = ctk.CTkScrollableFrame(
            self.tabview.tab("Basic"), label_text="Selected File(s)"
        )
        self.scrollable_frame.grid(row=1, column=0, sticky="nsew", padx=5)
        self.scrollable_frame.grid_columnconfigure(0, weight=1)

    def _setup_settings_tab(self):
        settings_frame = ctk.CTkFrame(
            self.tabview.tab("Settings"), fg_color="transparent"
        )
        settings_frame.grid(row=0, column=0, sticky="nsew")
        settings_frame.grid_columnconfigure(0, weight=1)

        settings = [
            (
                "Command Connector Retention:",
                0,
                ["None", "30", "60", "90"],
                self.set_recommend_cc_retention,
            ),
            (
                "Appearance Mode:",
                4,
                ["System", "Light", "Dark"],
                change_appearance_mode_event,
            ),
        ]
        for text, row, options, command in settings:
            ctk.CTkLabel(settings_frame, text=text, anchor="w").grid(
                row=row, column=0, sticky="nsew", pady=(0, 5)
            )
            if options:
                ctk.CTkOptionMenu(
                    settings_frame, values=options, command=command
                ).grid(row=row + 1, column=0, sticky="new", pady=(0, 15))

        # Add Force Column entry field
        ctk.CTkLabel(settings_frame, text="Force Column:", anchor="w").grid(
            row=2, column=0, sticky="nsew", pady=(0, 5)
        )
        self.force_column_entry = ctk.CTkEntry(
            settings_frame, placeholder_text="Enter Camera Column Number"
        )
        self.force_column_entry.grid(
            row=3, column=0, sticky="new", pady=(0, 15)
        )

    def _create_main_window(self):
        # Main frame
        self.main_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.main_frame.grid(row=0, column=1, sticky="nsew", padx=5)
        self.main_frame.grid_rowconfigure(
            1, weight=1
        )  # Make bottom section expandable
        self.main_frame.grid_columnconfigure(0, weight=1)

        # Top section
        self.top_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        self.top_frame.grid(row=0, column=0, sticky="nsew")
        self.top_frame.grid_columnconfigure(
            0, weight=1
        )  # Make page label expandable

        self.page_label = ctk.CTkLabel(
            self.top_frame,
            text="No File Selected",
            font=ctk.CTkFont(size=13),
            fg_color=("gray85", "gray20"),
            corner_radius=6,
        )
        self.page_label.grid(row=0, column=0, sticky="ew", padx=5, pady=5)

        self.export_button = ctk.CTkButton(
            self.top_frame, text="Export", command=self.export_event
        )
        self.export_button.grid(row=0, column=1, sticky="e", padx=5, pady=5)

        # Bottom section
        self.bottom_frame = ctk.CTkFrame(self.main_frame)
        self.bottom_frame.grid(row=1, column=0, sticky="nsew", padx=5, pady=5)
        self.bottom_frame.grid_rowconfigure(
            0, weight=1
        )  # Make content expandable vertically
        self.bottom_frame.grid_columnconfigure(
            0, weight=6
        )  # Camera list gets more space
        self.bottom_frame.grid_columnconfigure(
            1, weight=1
        )  # Info panel gets less space

        # Left side - Compatible Cameras
        self.output_scrollable = ctk.CTkScrollableFrame(
            self.bottom_frame, label_text="Camera Compatibility List"
        )
        self.output_scrollable.grid(
            row=0, column=0, sticky="nsew", padx=5, pady=5
        )
        self.output_scrollable.grid_columnconfigure(
            0, weight=1
        )  # Make content expand horizontally

        # Right side - Information Panel
        self.info_panel = ctk.CTkFrame(self.bottom_frame)
        self.info_panel.grid(
            row=0, column=1, sticky="nsew", padx=5, pady=5
        )  # Changed to nsew
        self.info_panel.grid_columnconfigure(
            0, weight=4
        )  # Make content expand horizontally
        self.info_panel.grid_rowconfigure(
            3, weight=1
        )  # Make camera details expand vertically

        # General Information Section
        self.general_info_label = ctk.CTkLabel(
            self.info_panel,
            text="General Information",
            fg_color=("gray85", "gray20"),
            corner_radius=6,
        )
        self.general_info_label.grid(
            row=0, column=0, sticky="ew", padx=5, pady=3
        )

        self.general_info_frame = ctk.CTkFrame(self.info_panel)
        self.general_info_frame.grid(
            row=1, column=0, sticky="ew", padx=5, pady=3
        )
        self.general_info_frame.grid_columnconfigure(0, weight=1)

        # Camera Details Section
        self.camera_details_label = ctk.CTkLabel(
            self.info_panel,
            text="Camera Details",
            fg_color=("gray85", "gray20"),
            corner_radius=6,
        )
        self.camera_details_label.grid(
            row=2, column=0, sticky="ew", padx=5, pady=3
        )

        self.camera_details_frame = ctk.CTkFrame(self.info_panel)
        self.camera_details_frame.grid(
            row=3, column=0, sticky="nsew", padx=5, pady=3
        )
        self.camera_details_frame.grid_columnconfigure(0, weight=1)
        self.camera_details_frame.grid_rowconfigure(0, weight=1)

        # Initialize storage for file information
        self.current_file_info = {
            "filename": "",
            "filesize": 0,
            "total_cameras": 0,
            "exact_matches": 0,
            "identified_matches": 0,
            "potential_matches": 0,
            "unsupported_matches": 0,
        }

    def update_general_info(self, file_path, camera_list):
        """Update the general information display."""
        # Clear previous information
        for widget in self.general_info_frame.winfo_children():
            widget.destroy()

        # Update file information
        self.current_file_info = {}
        self.current_file_info["filename"] = os.path.basename(file_path)
        self.current_file_info["filesize"] = (
                os.path.getsize(file_path) / 1024
        )  # Convert to KB

        # Count different types of matches
        if not camera_list.empty:
            match_counts = (
                camera_list.groupby("match_type")["count"].sum().to_dict()
            )
        else:
            match_counts = {}

        self.current_file_info["exact_matches"] = match_counts.get(
            "exact", 0
        )
        self.current_file_info["identified_matches"] = match_counts.get(
            "identified", 0
        )
        self.current_file_info["potential_matches"] = match_counts.get(
            "potential", 0
        )
        self.current_file_info["unsupported_matches"] = match_counts.get(
            "unsupported", 0
        )

        self.current_file_info["total_cameras"] = (
                self.current_file_info["exact_matches"]
                + self.current_file_info["identified_matches"]
                + self.current_file_info["potential_matches"]
                + self.current_file_info["unsupported_matches"]
        )

        # Display information
        info_text = [
            f"File: {self.current_file_info['filename']} \
            ({self.current_file_info['filesize']:.2f} KB)",
            f"Total Cameras: {self.current_file_info['total_cameras']}",
            "Camera Breakdown:",
            f"  - Exact Matches: {self.current_file_info['exact_matches']}",
            f"  - Identified Matches: {self.current_file_info['identified_matches']}",
            f"  - Potential Matches: {self.current_file_info['potential_matches']}",
            f"  - Unsupported Matches: {self.current_file_info['unsupported_matches']}",
        ]

        # If recommendations are enabled
        if (
                hasattr(self, "recommend_cc_value")
                and self.recommend_cc_value != 0
        ):
            memory = MemoryStorage()
            recommend_connectors(
                True,
                self.recommend_cc_value,
                self.current_camera_list,
                self.verkada_compatibility_list,
                memory,
            )
            recommendations = memory.print_recommendations()
            if recommendations:
                info_text.append("\nRecommended Connectors:")
                for recommendation in recommendations:
                    info_text.append(
                        f"  - {recommendation[0]}: {recommendation[1]}"
                    )
                info_text.append(
                    f"\nExcess Channels: {memory.get_excess_channels()}"
                )

        # Create label with updated info
        ctk.CTkLabel(
            self.general_info_frame,
            text="\n".join(info_text),
            anchor="w",
            justify="left",
            wraplength=400,
        ).pack(fill="both", padx=5, pady=5)

    def select_files_event(self):
        """
        Shows files selected by the user and sets them as a button.
        :return:
        """
        if files := filedialog.askopenfilenames(
                title="Choose files to Run", filetypes=[("CSV files", "*.csv")]
        ):
            # Clean Previous Files
            self.file_paths.clear()
            for widget in self.scrollable_frame.winfo_children():
                widget.destroy()

            # Add Files
            for count, file in enumerate(files):
                self.file_paths.append(file)
                filename = os.path.basename(file)
                ctk.CTkButton(
                    self.scrollable_frame,
                    text=filename,
                    command=lambda f=file: self.run_compatibility_check(f),
                ).grid(row=count, column=0, sticky="ew", pady=2)
                self.scrollable_frame.configure(
                    label_text=f"Selected Files ({len(self.file_paths)}):"
                )

    def run_compatibility_check(self, file_path):
        """
        Run a compatibility check for the provided customer camera list.
        :param file_path:
        :return:
        """
        self.page_label.configure(text=f"{os.path.basename(file_path)}")

        if (
                self.force_column_entry.get() is None
                or self.force_column_entry.get().strip() == ""
        ):
            self.force_column_value = None
        else:
            self.force_column_value = int(self.force_column_entry.get())

        if file_path:
            matched_cameras = get_camera_match(
                parse_customer_list(file_path),
                self.verkada_compatibility_list,
                self.force_column_value,
            )
            if matched_cameras is not None:
                self.current_camera_list = (
                    matched_cameras  # Store for reference
                )
                self.populate_table(matched_cameras)
                self.update_general_info(file_path, matched_cameras)
                print(matched_cameras)

    def add_row_to_scrollable_frame(
            self, frame, camera_name, verkada_camera, colors
    ):
        """Add a new row to the scrollable frame with camera information.
        Args:
            frame: The parent frame to add the row to
            camera_name: Name of the camera
            verkada_camera: Corresponding Verkada camera model
            colors: Tuple of colors for the row background
        """
        row_frame = ctk.CTkFrame(frame, fg_color=colors, corner_radius=6)
        row_frame.grid_columnconfigure(0, weight=1)
        camera_button = ctk.CTkButton(
            row_frame,
            text=f"{camera_name} ({verkada_camera})",
            anchor="w",
            command=lambda f=camera_name: self.show_camera_details(f),
            fg_color=colors,
            hover_color=colors[::-1],
            text_color=("#000000", "#ffffff"),
        )
        camera_button.grid(row=0, column=0, sticky="ew")
        row_frame.pack(fill="x", padx=5, pady=2)

    def show_camera_details(self, camera_name):
        """
        Shows the camera details for the specified camera.
        :param camera_name:
        :return:
        """
        # Clear previous camera details
        for widget in self.camera_details_frame.winfo_children():
            widget.destroy()

        # Find camera in the current data
        camera_data = None
        for _, row in self.current_camera_list.iterrows():
            if row["name"] == camera_name:
                camera_data = row
                break

        if camera_data is not None:
            # Get Verkada details
            verkada_details = list_verkada_camera_details(
                camera_data["verkada_model"], self.verkada_compatibility_list
            )

            # Display camera information
            details = [
                f"Name: {camera_name}",
                f"Count: {int(camera_data['count'])}",
                f"Match Type: {camera_data['match_type']}",
            ]
            if camera_data["match_type"] != "unsupported":
                details = details + [
                    "Verkada Verified Details:",
                    f"  - Name: {camera_data['verkada_model']}",
                    f"  - Manufacturer: {verkada_details[1]}",
                    f"  - Min. Firmware: {verkada_details[2]}",
                    f"  - Notes: {verkada_details[3]}",
                ]
            (
                ctk.CTkLabel(
                    self.camera_details_frame,
                    text="\n".join(details),
                    anchor="w",
                    justify="left",
                    wraplength=400,
                ).pack(fill="both", padx=5, pady=5)
            )

    def populate_table(self, camera_list: pandas.DataFrame):
        """
        Populate the table with camera information from the DataFrame.

        Args:
            camera_list: DataFrame containing camera information
        """
        for widget in self.output_scrollable.winfo_children():
            widget.destroy()

        for _, row in camera_list.iterrows():
            color = self._get_color_for_match_type(row["match_type"])
            self.add_row_to_scrollable_frame(
                self.output_scrollable,
                row["name"],
                row["verkada_model"],
                color
            )

    def set_recommend_cc_retention(self, value):
        """
        Set the recommendation retention value.

        Args:
            value: Retention value as string ("None" or number of days)
        """
        self.recommend_cc_value = 0 if value == "None" else int(value)

    def set_force_column(self, value):
        """
        Set the force column value for data processing.

        Args:
            value: Column number to force
        """
        self.force_column_value = value

    def export_event(self):
        """
        Export the current camera list to a CSV file.
        Prompts user for save location and exports data.
        """
        cameras_dataframe = self.current_camera_list
        files = [("CSV files", "*.csv"), ("All Files", "*.*")]
        filepath = filedialog.asksaveasfilename(filetypes=files)
        if filepath:
            export_to_csv(cameras_dataframe, filepath)

    def _get_color_for_match_type(self, match_type: str) -> tuple:
        """
        Get the color scheme for a given match type.

        Args:
            match_type: Type of camera match

        Returns:
            tuple: Pair of colors for normal and hover states
        """
        color_map = {
            "exact": ("#a0e77d", "#61724C"),     # Green
            "identified": ("#82b6d9", "#4C4E72"), # Blue
            "potential": ("#ebd671", "#726E4C"),  # Yellow
            "unsupported": ("#ef8677", "#724C4C") # Red
        }
        return color_map.get(match_type, ("#ffffff", "#000000"))

def change_appearance_mode_event(mode):
    """
    Change the application's appearance mode.

    Args:
        mode: The appearance mode to set ("System", "Light", or "Dark")
    """
    ctk.set_appearance_mode(mode)


if __name__ == "__main__":
    app = App()
    app.mainloop()
