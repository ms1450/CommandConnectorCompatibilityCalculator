"""
Author: Ian Young
Co-Author: Mehul Sen
Purpose: Create a GUI through which the application may be ran and managed.
"""

# pylint: disable=ungrouped-imports

from os.path import basename
from subprocess import check_call
from sys import executable
from tkinter import (
    LEFT,
    RIGHT,
    Button,
    Frame,
    Label,
    Scrollbar,
    Text,
    Y,
    filedialog,
)

try:
    from colorama import Fore, Style, init
    from tkinterdnd2 import DND_FILES, TkinterDnD
    from ttkthemes import ThemedStyle
except ImportError as e:
    package_name = str(e).split()[-1]
    check_call([executable, "-m", "pip", "install", package_name])
    # Import again after installation
    from colorama import Fore, Style, init
    from tkinterdnd2 import DND_FILES, TkinterDnD
    from ttkthemes import ThemedStyle

from app import log
from app.calculations import compile_camera_mp_channels, get_camera_match
from app.file_handling import (
    parse_customer_list,
    parse_hardware_compatibility_list,
)
from app.formatting import get_manufacturer_set, sanitize_customer_data
from app.output import print_results
from app.recommend import recommend_connectors


# Initialize colorized output
init(autoreset=True)
RETENTION = 30


class CameraCompatibilityApp:
    """A GUI application for checking camera compatibility based on CSV files.

    This application allows users to select a CSV file, drop it into the
    interface, and run a compatibility check to display results.

    Args:
        root (Tk): The root window of the application.

    Methods:
        select_file: Opens a file dialog to select a customer CSV file.
        on_drop: Handles the event when a file is dropped onto the
            application window.
        run_check: Executes the compatibility check using the selected
            customer file and displays the results.
    """

    def __init__(self, window):
        """Initializes the CameraCompatibilityApp for checking compatibility.

        This constructor sets up the main window, including buttons for
        file selection and running compatibility checks, as well as a
        text widget for displaying results.

        Args:
            window (Tk): The window window of the application.

        Returns:
            None
        """
        self.root = window
        self.root.title("Camera Compatibility Checker")
        self.customer_file_path = None

        style = ThemedStyle(window)
        style.set_theme("arc")

        self.label = Label(window, text="Select or Drop Customer CSV File")
        self.label.pack(pady=20)

        # Create a frame for the buttons
        button_frame = Frame(window)
        button_frame.pack(pady=10)

        self.button = Button(
            button_frame, text="Select File", command=self.select_file
        )
        self.button.pack(pady=5)

        window.drop_target_register(DND_FILES)
        window.dnd_bind("<<Drop>>", self.on_drop)

        self.submit_button = Button(
            button_frame,
            text="Run Compatibility Check",
            command=self.run_check,
        )
        self.submit_button.pack_forget()  # Hide the button

        # Scrollable text frame for results
        frame = Frame(window)
        frame.pack(fill="both", expand=True)

        self.text_widget = Text(
            frame, wrap="none"
        )  # Prevent text from wrapping
        self.text_widget.pack(side=LEFT, fill="both", expand=True)
        self.text_widget.config(height=15, state="disabled")

        scrollbar = Scrollbar(
            frame, orient="vertical", command=self.text_widget.yview
        )
        scrollbar.pack(side=RIGHT, fill=Y)

        self.text_widget.config(yscrollcommand=scrollbar.set)

    def select_file(self):
        """Opens a file dialog for the user to select a CSV file.

        If a file is selected, it updates the internal file path and the
        label to reflect the selected file.

        Args:
            None

        Returns:
            None
        """
        if file_path := filedialog.askopenfilename(
            filetypes=[("CSV files", "*.csv")]
        ):
            self.customer_file_path = file_path
            self.label.config(text=f"Selected: {file_path}")

    def on_drop(self, event):
        """
        Handles the event when a file is dropped onto the window.

        This function updates the internal file path with the dropped
        file's path and updates the label to indicate the file has
        been dropped.

        Args:
            event: The event object containing information about the
                drop action.

        Returns:
            None
        """
        self.customer_file_path = event.data.strip("{}")
        self.label.config(
            text=f"Selected: {basename(self.customer_file_path)}"
        )
        self.submit_button.pack()

    def run_check(self):
        """
        Executes the compatibility check using the selected file.

        This function verifies if a file has been selected, processes the
        compatibility data, and updates the GUI with the results or logs
        an error if no matches are found.

        Args:
            None

        Returns:
            None

        Raises:
            None
        """
        if not self.customer_file_path:
            log.critical("%sNo file selected.%s", Fore.RED, Style.RESET_ALL)
            return

        verkada_compatibility_list = compile_camera_mp_channels(
            parse_hardware_compatibility_list(
                "Verkada Command Connector Compatibility.csv"
            )
        )

        customer_cameras_list = sanitize_customer_data(
            parse_customer_list(self.customer_file_path),
            get_manufacturer_set(verkada_compatibility_list),
        )

        matched_cameras = get_camera_match(
            customer_cameras_list, verkada_compatibility_list
        )

        if matched_cameras is not None:
            # Clear previous text before displaying new results
            self.text_widget.config(state="normal")
            self.text_widget.delete(1.0, "end")

            # Display the results in the text widget
            print_results(
                matched_cameras,
                verkada_compatibility_list,
                self.text_widget,
                self.root,
            )

            recommend_connectors(matched_cameras, verkada_compatibility_list)
        else:
            log.critical(
                "%sCould not identify model column.%s",
                Fore.RED,
                Style.RESET_ALL,
            )


if __name__ == "__main__":
    root = TkinterDnD.Tk()  # Initialize TkinterDnD for drag-and-drop support
    app = CameraCompatibilityApp(root)
    root.mainloop()
