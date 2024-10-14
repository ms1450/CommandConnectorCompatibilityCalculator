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

# Importing modules and functions from other parts of the application
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
)
from app.memory_management import MemoryStorage
from app.recommend import (
    count_mp,
    recommend_connectors,
    calculate_4k_storage,
    calculate_low_mp_storage,
)

# Initialize colorama to auto-reset color settings in terminal output
init(autoreset=True)

# Constant strings for GUI labels and error messages
SELECT_CSV_TEXT = "Select CSV"
RUN_CHECK_TEXT = "Run Check"
ERROR_NO_FILE = "Error: No File Selected."
PROCESSING_TEXT = "Processing... Please Wait"
COMPLETED_TEXT = "Completed"
ERROR_PROCESSING = "Error: Could not process file"
DEFAULT_FILE_STATUS = "No File Selected"
DETAILS_LABEL = "Additional Details"


class CameraCompatibilityApp:
    """A class to manage the GUI for Command Connector Compatibility Calculator.

    This class provides methods to set up the GUI and run the main tool
    using tkinter.
    """

    def __init__(self, window):
        """Initializes the Camera Compatibility class.

        Args:
            window: The main window object for the GUI.

        Initializes UI components, sets up variables, and configures memory storage.
        """
        self.root = window
        self.change_detected_flag = (
            True  # Tracks if changes have been made to rerun checks
        )
        self.customer_file_path: Optional[str] = (
            None  # Path to the selected customer CSV file
        )
        self.file_status = StringVar(
            value=DEFAULT_FILE_STATUS
        )  # Status text for file selection
        self.recommendation_enabled = IntVar(
            value=0
        )  # Variable to store the state of recommendation checkbox
        self.item_details = (
            {}
        )  # Dictionary to store detailed camera information
        self.memory = (
            MemoryStorage()
        )  # Initialize memory storage for recommendation process
        self._setup_ui()  # Calls method to set up the user interface
        self.toggle_recommendation_visibility()  # Set the visibility of recommendation UI elements based on checkbox

    def _setup_ui(self):
        """Sets up the main UI elements for the application."""
        self.root.title(
            "Command Connector Compatibility Calculator"
        )  # Set the window title
        self.root.geometry("900x700")  # Set the window size

        # Apply a themed style to the window
        style = ThemedStyle(self.root)
        style.set_theme("equilux")  # Dark theme
        style.configure(
            "RunButton.TButton",
            background="#fffcff",
            font=("Helvetica", 14, "bold"),
        )

        # Call methods to create the different UI elements
        self._create_widgets()
        self._setup_layout()
        self._configure_drag_and_drop()

    def _create_widgets(self):
        """Creates the widgets (buttons, labels, frames) for the UI."""
        self.main_frame = ttk.Frame(
            self.root, padding="10"
        )  # Main container for UI elements
        self.file_frame = (
            self._create_file_frame()
        )  # Frame for file selection UI
        self.options_frame = (
            self._create_options_frame()
        )  # Frame for additional options (checkboxes)
        self.run_button = ttk.Button(  # Run button to trigger file processing
            self.main_frame,
            text=RUN_CHECK_TEXT,
            command=self.run_check,
            state="disabled",  # Initially disabled until a file is selected
            style="RunButton.TButton",
        )
        self.result_frame = (
            self._create_result_frame()
        )  # Frame for displaying results
        self.details_frame = (
            self._create_details_frame()
        )  # Frame for displaying additional details
        self.status_label = ttk.Label(  # Label to display status messages
            self.main_frame, text="", font=("Helvetica", 14, "italic")
        )
        self.recommendation_frame = (
            self._create_recommendation_frame()
        )  # Frame for displaying recommendations

    def _create_file_frame(self) -> Frame:
        """Creates the file selection frame.

        This frame contains a label to display file status and a button to open the file dialog.
        """
        file_frame = ttk.Frame(self.main_frame)
        ttk.Label(
            file_frame, textvariable=self.file_status, font=("Helvetica", 14)
        ).pack(side=LEFT, fill=X, expand=True)
        ttk.Button(
            file_frame, text=SELECT_CSV_TEXT, command=self.select_file
        ).pack(side=RIGHT)
        return file_frame

    def _create_options_frame(self) -> Frame:
        """Creates the options frame.

        Includes a checkbox for enabling recommendations and input for retention period.
        """
        options_frame = ttk.Frame(self.main_frame)

        # Frame for retention period input (spinbox for number of days)
        self.retention_frame = ttk.Frame(options_frame)
        self.retention_label = ttk.Label(
            self.retention_frame,
            text="Retention Period (days):",
            font=("Helvetica", 14),
        )
        self.retention_label.pack(side=LEFT, padx=(0, 10))
        self.retention = IntVar(
            value=30
        )  # Default retention period of 30 days
        self.retention_spinbox = ttk.Spinbox(
            self.retention_frame,
            from_=30,
            to=90,
            increment=30,
            textvariable=self.retention,
            width=5,
            command=self.change_detected,  # Mark changes when retention period is modified
        )
        self.retention_spinbox.pack(side=LEFT, padx=(0, 20))
        self.retention_frame.pack(
            side=LEFT
        )  # Initially packed, will be toggled

        # Checkbox to enable/disable recommendations
        self.recommendation_checkbox = ttk.Checkbutton(
            options_frame,
            text="Recommend CCs",
            variable=self.recommendation_enabled,
            command=self.toggle_recommendation_visibility,  # Change visibility when checkbox is toggled
        )
        self.recommendation_checkbox.pack(side=LEFT)
        return options_frame

    def _create_result_frame(self) -> Frame:
        """Creates the frame to display the results (matched cameras).

        Includes a Treeview widget with scrollbars.
        """
        result_frame = ttk.Frame(self.main_frame)
        self.treeview = ttk.Treeview(
            result_frame,
            columns=("Name", "Count", "Matched Model"),
            show="headings",
        )
        # Setting up the Treeview columns and headers
        for col in self.treeview["columns"]:
            self.treeview.heading(col, text=col)
        self.treeview.column("Name", width=250)
        self.treeview.column("Count", width=100, anchor="center")
        self.treeview.column("Matched Model", width=250)

        # Adding scrollbars to the Treeview
        self.scrollbar_y = ttk.Scrollbar(
            result_frame, orient="vertical", command=self.treeview.yview
        )
        self.scrollbar_x = ttk.Scrollbar(
            result_frame, orient="horizontal", command=self.treeview.xview
        )
        self.treeview.configure(
            yscrollcommand=self.scrollbar_y.set,
            xscrollcommand=self.scrollbar_x.set,
        )

        self.treeview.pack(side=LEFT, fill=BOTH, expand=True)
        self.scrollbar_y.pack(side=RIGHT, fill=Y)
        self.scrollbar_x.pack(side=BOTTOM, fill=X)
        return result_frame

    def _create_details_frame(self) -> Frame:
        """Creates the details frame to display additional information about the selected camera."""
        details_frame = ttk.Frame(self.main_frame, padding="10")
        ttk.Label(
            details_frame, text=DETAILS_LABEL, font=("Helvetica", 14)
        ).pack(anchor="w")
        self.details_text = Text(
            details_frame, wrap=WORD, height=6, font=("Helvetica", 14)
        )
        self.details_text.config(state=DISABLED)  # Initially disabled
        self.details_text.pack(fill=BOTH, expand=True, pady=5)
        return details_frame

    def _create_recommendation_frame(self) -> Frame:
        """Creates the frame to display recommendations for connectors."""
        recommendation_frame = ttk.Frame(self.main_frame, padding="10")
        ttk.Label(
            recommendation_frame,
            text="Command Connector Recommendations",
            font=("Helvetica", 14, "bold"),
        ).pack(anchor="w")

        self.recommendation_text = Text(
            recommendation_frame, wrap=WORD, height=4, font=("Helvetica", 14)
        )
        self.recommendation_text.config(state=DISABLED)  # Initially disabled
        self.recommendation_text.pack(fill=BOTH, expand=True, pady=5)
        return recommendation_frame

    def _setup_layout(self):
        """Arranges the layout of the main UI frames."""
        self.main_frame.pack(fill=BOTH, expand=True)
        self.file_frame.pack(fill=X, pady=(0, 10))
        self.options_frame.pack(fill=X, pady=(0, 10))
        self.run_button.pack(fill=X, pady=(0, 10))
        self.result_frame.pack(fill=BOTH, expand=True)
        self.details_frame.pack(fill=X, pady=(10, 0))
        # self.recommendation_frame.pack(fill=X, pady=(10, 0))  # Initially not packed
        self.status_label.pack(fill=X, pady=(10, 0))

    def _configure_drag_and_drop(self):
        """Configures drag-and-drop functionality for file selection."""
        self.root.drop_target_register(
            DND_FILES
        )  # Register window as a drop target
        self.root.dnd_bind("<<Drop>>", self.on_drop)  # Bind the drop event

    def on_drop(self, event):
        """Handles file drop events."""
        self.change_detected()
        self._update_file_selection(
            event.data.strip("{}")
        )  # Strip the curly braces from dropped file path

    def select_file(self):
        """Opens a file dialog for selecting a customer CSV file."""
        self.change_detected()
        file_path = filedialog.askopenfilename(
            filetypes=[("CSV files", "*.csv")]
        )
        if file_path:
            self._update_file_selection(file_path)

    def _update_file_selection(self, file_selection: str):
        """Updates the file selection label and enables the run button."""
        self.customer_file_path = file_selection  # Store selected file path
        self.file_status.set(
            f"Selected: {os.path.basename(self.customer_file_path)}"
        )  # Display file name
        self.run_button.config(
            state="normal", style="RunButton.TButton"
        )  # Enable the run button
        self.status_label.config(  # Update the status label with file loaded message
            text="File loaded. Click 'Run Check' to process.",
            foreground="#ccffcc",
            font=("Helvetica", 14),
        )

    @time_function
    def run_check(self):
        """Runs the compatibility check when the 'Run Check' button is clicked.

        This function processes the customer CSV file, compares it against the compatibility list,
        and displays the results in the Treeview.
        """
        # Check if a customer file has been selected
        if not self.customer_file_path:
            self.status_label.config(
                text=ERROR_NO_FILE,
                foreground="#ffcccc",
                font=("Helvetica", 14),
            )
            return

        # Update status to show processing message
        self.status_label.config(
            text=PROCESSING_TEXT, foreground="#fff2cc", font=("Helvetica", 14)
        )
        self.root.update()

        try:
            # Load the Verkada compatibility list, prompting user if not found
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

            # Process compatibility list and customer cameras
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
                # Display the results and status
                self._display_results(
                    matched_cameras, verkada_compatibility_list
                )
                self.status_label.config(
                    text=COMPLETED_TEXT,
                    foreground="#ccffcc",
                    font=("Helvetica", 14),
                )

                # If recommendations are enabled, perform recommendations
                if self.recommendation_enabled.get():
                    self._perform_recommendations(
                        matched_cameras, verkada_compatibility_list
                    )
                else:
                    self.recommendation_text.config(state=NORMAL)
                    self.recommendation_text.delete(1.0, END)
                    self.recommendation_text.insert(
                        END, "Recommendations not enabled."
                    )
                    self.recommendation_text.config(state=DISABLED)
            else:
                self.status_label.config(
                    text=ERROR_PROCESSING,
                    foreground="#ffcccc",
                    font=("Helvetica", 14),
                )
        except Exception as e:
            log.error(
                "Error in run_check: %s", str(e)
            )  # Log any errors encountered
            self.status_label.config(
                text=f"Error: {str(e)}",
                foreground="#ffcccc",
                font=("Helvetica", 14),
            )
        self.toggle_change()

    def _display_results(
        self,
        matched_cameras: pd.DataFrame,
        verkada_list: List[CompatibleModel],
    ):
        """Displays the matched cameras in the Treeview widget."""
        self.treeview.delete(
            *self.treeview.get_children()
        )  # Clear previous entries
        self._configure_tags()  # Set up color tags for different match types

        for _, row in matched_cameras.iterrows():
            # Get Verkada camera details for the matched row
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

            # Assign a tag based on the match type
            match_type = row.get("match_type", "unknown").lower()
            tag = self._get_tag_for_match_type(str(match_type))

            # Insert the camera row into the Treeview
            item_id = self.treeview.insert(
                "",
                "end",
                values=(row["name"], int(row["count"]), row["verkada_model"]),
                tags=(tag,),
            )
            self.item_details[item_id] = (
                details  # Store details for later display
            )

        self.treeview.bind(
            "<ButtonRelease-1>", self.on_tree_click
        )  # Bind click events to display details

    def _configure_tags(self):
        """Configures tags to color-code the Treeview rows based on match type."""
        self.treeview.tag_configure("unsupported", foreground="#ff4d4d")
        self.treeview.tag_configure("potential", foreground="#ffcc00")
        self.treeview.tag_configure("exact", foreground="#33cc33")
        self.treeview.tag_configure("identified", foreground="#3399ff")

    def _get_tag_for_match_type(self, match_type: str) -> Optional[str]:
        """Returns the appropriate tag for a given match type."""
        tag_map = {
            "unsupported": "unsupported",
            "potential": "potential",
            "exact": "exact",
            "identified": "identified",
        }
        return tag_map.get(match_type, None)

    def on_tree_click(self, event):
        """Handles clicks on the Treeview rows to display additional camera details."""
        item = self.treeview.identify_row(event.y)
        if item:
            details = self.item_details.get(item)
            if details:
                self.display_details(details)

    def display_details(self, details):
        """Displays the details of the selected camera in the details text box."""
        self.details_text.config(state=NORMAL)
        self.details_text.delete(1.0, END)

        details_text = "\n".join(
            f"{key}: {value}" for key, value in details.items()
        )

        self.details_text.insert(END, details_text)
        self.details_text.config(state=DISABLED)

    def _perform_recommendations(
        self,
        matched_cameras: pd.DataFrame,
        verkada_list: List[CompatibleModel],
    ):
        """Performs the recommendation of connectors based on matched cameras and retention period."""
        # Count the number of low and high MP cameras
        low_mp_count, high_mp_count = count_mp(matched_cameras, verkada_list)
        retention_days = self.retention.get()

        # Calculate the storage requirements based on camera count and retention period
        low_storage = calculate_low_mp_storage(low_mp_count, retention_days)
        high_storage = calculate_4k_storage(high_mp_count, retention_days)
        total_storage = low_storage + high_storage

        # Perform the connector recommendation based on the calculated storage
        recommend_connectors(
            change=True,
            retention=retention_days,
            camera_dataframe=matched_cameras,
            verkada_camera_list=verkada_list,
            memory=self.memory,
        )

        # Retrieve and display the recommendations and excess channels
        recommendations = self.memory.get_recommendations()
        excess_channels = self.memory.get_excess_channels()

        self.recommendation_text.config(state=NORMAL)
        self.recommendation_text.delete(1.0, END)

        if recommendations:
            rec_text = "Recommended Command Connectors:\n"
            rec_text += "\n".join([conn["name"] for conn in recommendations])
            rec_text += f"\n\nExcess Channels: {excess_channels}"
            self.recommendation_text.insert(END, rec_text)
        else:
            self.recommendation_text.insert(
                END, "No recommendations available."
            )

        self.recommendation_text.config(state=DISABLED)

    def toggle_recommendation_visibility(self):
        """Toggles the visibility of the recommendation UI elements based on the checkbox state."""
        if self.recommendation_enabled.get():
            self.retention_frame.pack(side=LEFT)
            self.recommendation_frame.pack(fill=X, pady=(10, 0))
        else:
            self.retention_frame.pack_forget()
            self.recommendation_frame.pack_forget()
        self.change_detected()

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
        self.status_label.config(
            text="Changes detected. Re-run the check for updated results.",
            foreground="#cce5ff",
        )


if __name__ == "__main__":
    root = TkinterDnD.Tk()
    app = CameraCompatibilityApp(root)
    root.mainloop()
