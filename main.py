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
    def __init__(self, root):
        self.root = root
        self.root.title("Camera Compatibility Checker")
        self.customer_file_path = None

        style = ThemedStyle(root)
        style.set_theme("arc")

        self.label = Label(root, text="Select or Drop Customer CSV File")
        self.label.pack(pady=20)

        self.button = Button(
            root, text="Select File", command=self.select_file
        )
        self.button.pack(pady=10)

        root.drop_target_register(DND_FILES)
        root.dnd_bind("<<Drop>>", self.on_drop)

        self.submit_button = Button(
            root, text="Run Compatibility Check", command=self.run_check
        )
        self.submit_button.pack(pady=20)

        # Scrollable text frame for results
        frame = Frame(root)
        frame.pack(fill="both", expand=True)

        self.text_widget = Text(
            frame, wrap="none"
        )  # Prevent text from wrapping
        self.text_widget.pack(side=LEFT, fill="both", expand=True)
        self.text_widget.config(height=15)

        scrollbar = Scrollbar(
            frame, orient="vertical", command=self.text_widget.yview
        )
        scrollbar.pack(side=RIGHT, fill=Y)

        self.text_widget.config(yscrollcommand=scrollbar.set)

    def select_file(self):
        if file_path := filedialog.askopenfilename(
            filetypes=[("CSV files", "*.csv")]
        ):
            self.customer_file_path = file_path
            self.label.config(text=f"Selected: {file_path}")

    def on_drop(self, event):
        self.customer_file_path = event.data.strip("{}")
        self.label.config(text=f"Dropped: {self.customer_file_path}")

    def run_check(self):
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
