from app.calculations import get_camera_match
from app.file_handling import *
from app.formatting import *
from app.output import *
from app.calculations import *

verkada_hardware_compatibility_list_filepath = (
    "../Verkada Command Connector Compatibility.csv"
)
verkada_camera_list = parse_hardware_compatibility_list(
    verkada_hardware_compatibility_list_filepath
)
verkada_camera_list = compile_camera_mp_channels(verkada_camera_list)

for count in range(1, 8):
    customer_list_filepath = (
        "../Camera Compatibility Sheets/customer_sheet_" + str(count) + ".csv"
    )
    customer_list = parse_customer_list(customer_list_filepath)

    manufacturer_set = get_manufacturer_set(verkada_camera_list)
    sanitized_customer_list = sanitize_customer_data(
        customer_list, manufacturer_set
    )

    camera_models = get_camera_match(
        sanitized_customer_list, verkada_camera_list
    )
    # print_results(camera_models, verkada_camera_list)
    recommend_connectors(camera_models, verkada_camera_list)
