from thefuzz import process
from thefuzz import fuzz
from tabulate import tabulate
import csv


class CompatibleModel:
    def __init__(self, model_name, manufacturer, minimum_supported_firmware_version, notes):
        self.model_name = model_name
        self.manufacturer = manufacturer
        self.minimum_supported_firmware_version = minimum_supported_firmware_version
        self.notes = notes

    def __str__(self):
        return self.model_name


# Get a list of camera models
def get_camera_list(compatible_models):
    if type(compatible_models) is list:
        camera_names = []
        for model in compatible_models:
            camera_names.append(model.model_name)
        return camera_names
    elif type(compatible_models) is dict:
        return list(compatible_models.keys())
    else:
        return []


def find_matching_camera(camera_name):
    global verkada_cameras
    for camera in verkada_cameras:
        if camera.model_name == camera_name.lower():
            return camera
    return "No Matching Camera Found"


# Parse the Hardware Compatibility List for the Command Connector
def parse_compatibility_list(filename):
    compatible_models = []
    with open(filename, newline='') as csvfile:
        reader = csv.reader(csvfile, delimiter=',')
        # Skip the first 5 rows
        for _ in range(5):
            next(reader)
        # Read the rest of the rows and create CompatibleModel objects
        for row in reader:
            model = CompatibleModel(row[1].lower(), row[0], row[2], row[3])
            compatible_models.append(model)
    return compatible_models


# Read the List of Customer Camera
def read_customer_list(filename):
    with open(filename, newline='') as csvfile:
        reader = csv.reader(csvfile)
        # Use zip(*reader) to transpose rows into columns
        columns = list(zip(*reader))

    # Convert each column from tuple to list
    return [list(column) for column in columns]


# Identify the Camera Model Column
def identify_model_column():
    global customer_cameras_raw
    global verkada_cameras_list
    scores = []
    for column_data in customer_cameras_raw:
        column_values = []
        column_score = 0
        for value in column_data:
            if value not in column_values:
                if value.strip():  # Check if value is not empty after stripping whitespace
                    score = process.extractOne(value, verkada_cameras_list, scorer=fuzz.token_sort_ratio)[1]
                    column_score += score
            else:
                column_values.append(value)
        scores.append(column_score)
    if scores:
        return scores.index(max(scores))
    else:
        print("No valid scores found. Check your input data.")
        return None


# Get Model and Statistics
def get_camera_count(column_number):
    global customer_cameras_raw
    camera_statistics = {}
    for value in customer_cameras_raw[column_number]:
        # Skip this value if it contains 'model' (case-insensitive)
        if 'model' in value.lower():
            continue

        # Strip leading and trailing whitespace
        value = value.strip()

        # Only process non-empty values
        if value:
            if value not in camera_statistics:
                camera_statistics[value] = 1
            else:
                camera_statistics[value] += 1
    return camera_statistics

# Complete Camera Match
# [Original Name, 'exact'/'identified'/'potential'/'unsupported', Camera Model]
def camera_match(list_customer_cameras):
    global verkada_cameras_list
    global traced_cameras
    for camera in list_customer_cameras:
        if camera != '':
            match, score = process.extractOne(camera, verkada_cameras_list, scorer=fuzz.ratio)
            sort_match, sort_score = process.extractOne(camera, verkada_cameras_list, scorer=fuzz.token_sort_ratio)
            set_match, set_score = process.extractOne(camera, verkada_cameras_list, scorer=fuzz.token_set_ratio)
            if score == 100 or sort_score == 100:
                traced_cameras.append([camera, 'exact', find_matching_camera(camera)])
                list_customer_cameras.remove(camera)
                continue
            elif set_score == 100:
                traced_cameras.append([camera, 'identified', find_matching_camera(match)])
                list_customer_cameras.remove(camera)
            elif score >= 80:
                traced_cameras.append([camera, 'potential', find_matching_camera(match)])
                list_customer_cameras.remove(camera)
            else:
                traced_cameras.append([camera, 'unsupported', ''])


def print_list_data():
    global customer_cameras
    global traced_cameras
    output = []
    for camera_data in traced_cameras:
        camera_name, camera_type, matched_camera = camera_data
        camera_count = str(customer_cameras.get(camera_name, 0))

        if isinstance(matched_camera, CompatibleModel):
            output.append([
                camera_name,
                camera_count,
                camera_type,
                matched_camera.manufacturer,
                matched_camera.model_name,
                matched_camera.minimum_supported_firmware_version,
                matched_camera.notes
            ])
        else:
            output.append([
                camera_name,
                camera_count,
                camera_type,
                '',
                '',
                '',
                ''
            ])

    # Define a custom sorting key
    def sort_key(item):
        order = {'exact': 0, 'identified': 1, 'potential': 2, 'unsupported': 3}
        return order.get(item[2], 4)  # Default to 4 if type is unknown

    # Sort the output list based on the custom sorting key
    output.sort(key=sort_key)

    print(tabulate(output, headers=['Camera Name', 'Camera Count', 'Supported Type', 'Manufacturer', 'Model', 'Firmware',
                            'Additional Notes']))

    with open('camera_models.txt', 'w') as f:
        f.write(tabulate(output, headers=['Camera Name', 'Camera Count', 'Supported Type', 'Manufacturer', 'Model', 'Firmware',
                            'Additional Notes']))

# Verkada Cameras
verkada_cameras = parse_compatibility_list('Verkada Command Connector Compatibility.csv')
verkada_cameras_list = get_camera_list(verkada_cameras)

# Customer Cameras
customer_cameras_raw = read_customer_list('./Camera Compatibility Sheets/Camera Compatibility Sheet 4.csv')
customer_cameras = get_camera_count(identify_model_column())
customer_cameras_list = get_camera_list(customer_cameras)

traced_cameras = []
camera_match(customer_cameras_list)
print_list_data()
print("\n")