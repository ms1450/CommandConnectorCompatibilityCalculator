"""
Author: Ian Young
Co-Author: Mehul Sen
Purpose: The contents of this file are to perform various calculations
    to inform the user how many Command Connectors will be required for
    a deal.
"""

# pylint: disable=ungrouped-imports

# Standard library imports
import re
from subprocess import check_call
from sys import executable
from typing import Dict, List, Optional, Union

# Third-party library imports
try:
    import colorama
    import numpy as np
    import pandas as pd
    from thefuzz import fuzz, process
except ImportError as e:
    package_name = str(e).split()[-1]
    check_call([executable, "-m", "pip", "install", package_name])
    # Import again after installation
    import colorama
    import numpy as np
    import pandas as pd
    from thefuzz import fuzz, process

# Local/application-specific imports
from app.formatting import get_camera_set, find_verkada_camera
from app import (
    log,
    logging_decorator,
    time_function,
    CompatibleModel,
    Connector,
)

# Initialize colorama
colorama.init(autoreset=True)


@time_function
def identify_model_column_name(
    customer_list: pd.DataFrame, verkada_cameras: List[CompatibleModel]
) -> Optional[Union[int, str]]:
    """Identify the column with the camera models in the customer list

    Args:
        customer_list (pd.DataFrame): The customer list to identify.
        verkada_cameras (List[CompatibleModel]): The list of verkada cameras.

    Returns:
        Optional[Series]: Column headers for the camera model column
    """
    verkada_camera_list = get_camera_set(verkada_cameras)

    def calculate_score(column_data: pd.Series) -> float:
        """Calculate the score of the column.

        Args:
            column_data (pd.DataFrame): The column to calculate the score.

        Returns:
            float: The calculated score.
        """
        # Remove empty strings and spaces
        cleaned_data = column_data.replace(["", " "], np.nan).dropna()

        # Check if the cleaned data is empty
        if cleaned_data.empty:
            return 0

        # Try to convert to numeric
        numeric_column = pd.to_numeric(cleaned_data, errors="coerce")

        # If all values are successfully converted to numeric, return 0
        if numeric_column.notna().all():
            log.info(
                "Detected Numeric Column '%s', Forcing Score: 0",
                column_data.name,
            )
            return 0

        column_values = set()
        column_score = 0

        for camera in column_data.dropna():  # Remove NaN values
            if isinstance(camera, str) and (
                camera and camera not in column_values
            ):
                score = process.extractOne(
                    camera,
                    list(verkada_camera_list),
                    scorer=fuzz.token_sort_ratio,
                )[1]
                column_score += score
                column_values.add(
                    camera
                )  # Add to set to avoid duplicate scoring

        return column_score

    # Apply the score calculation to each column in the DataFrame
    scores = customer_list.apply(calculate_score)
    log.info("Scores: \n '%s'", scores.to_string())

    # Get the index of the column with the highest score
    if not scores.empty and scores.max() > 0:
        return scores.idxmax()
    log.warning("%sNo valid scores found.%s Check your input data.")
    return None


@logging_decorator
def identify_count_column(customer_list: pd.DataFrame) -> Optional[int]:
    """Identify the column with the number of cameras in the customer list

    Args:
        customer_list (pd.DataFrame): The customer list to identify.

    Returns:
        Optional[Series]: Column headers for the camera count column
    """
    # Case-insensitive pattern to search for count-related terms
    count_column_pattern = re.compile(r"(?i)\bcount\b|#|\bquantity\b")

    return next(
        (
            col_num
            for col_num, col in enumerate(customer_list.columns)
            if isinstance(col, str) and count_column_pattern.search(col)
        ),
        None,
    )


def get_camera_count(
    customer_list: pd.DataFrame, results: pd.DataFrame
) -> pd.DataFrame:
    """Count the occurrences of camera names in a specified column.

    Args:
        customer_list (pd.DataFrame): The customer list to identify.
        results (pd.DataFrame): The results of the calculation of camera models.

    Returns:
        Dict[str, int]: A dictionary containing camera names and counts.
    """
    if count_column_index := identify_count_column(customer_list):
        log.info(
            "Found Camera Count Column: %s",
            customer_list.columns[count_column_index],
        )
        # Convert count column to numeric, replacing non-numeric values with 1
        count_column: pd.Series = pd.to_numeric(
            customer_list.iloc[:, count_column_index], errors="coerce"
        ).fillna(1)

        camera_counts_dict = {
            name: count_column.iloc[group].sum()
            for name, group in results.groupby("name").groups.items()
        }
        # Convert dictionary to DataFrame and merge
        camera_counts = pd.DataFrame(
            list(camera_counts_dict.items()), columns=["name", "count"]
        )
        results = results.merge(camera_counts, on="name", how="left")
    else:
        log.info("No Camera Count Found, calculating using model names")
        results["count"] = results.groupby("name")["name"].transform("count")

        # Keep only unique camera names
    results = results.drop_duplicates(["name"])

    # Filter out rows where name is NA and match_type is "empty"
    results = results[
        (results["name"].notna()) | (results["match_type"] != "empty")
    ]

    return results


def get_camera_match(
    customer_list: pd.DataFrame,
    verkada_cameras: List[CompatibleModel],
    model_column: Optional[Union[int, str]] = None,
) -> pd.DataFrame:
    """Match customer cameras against a list of known Verkada cameras.

    Args:
        customer_list (pd.DataFrame): The list of known cameras.
        verkada_cameras (List[CompatibleModel]): The list of known cameras.
        model_column (Optional[int]): The column index of the known camera model.

    Returns:
        pd.DataFrame: The matched cameras with count.

    Raises:
        ValueError: If the specified column index is out of bounds.
        KeyError: If the specified column name is not found in the DataFrame.
    """

    def match_camera(camera):
        if pd.isna(camera) or camera == "":
            return pd.Series(
                {"name": None, "match_type": "empty", "verkada_model": None}
            )

        match, score = process.extractOne(
            camera, verkada_cameras_list, scorer=fuzz.ratio
        )
        _, sort_score = process.extractOne(
            camera, verkada_cameras_list, scorer=fuzz.token_sort_ratio
        )
        _, set_score = process.extractOne(
            camera, verkada_cameras_list, scorer=fuzz.token_set_ratio
        )
        if score == 100 or sort_score == 100:
            return pd.Series(
                {
                    "name": camera,
                    "match_type": "exact",
                    "verkada_model": match,
                }
            )
        if set_score == 100:
            return pd.Series(
                {
                    "name": camera,
                    "match_type": "identified",
                    "verkada_model": match,
                }
            )
        if score >= 80:
            return pd.Series(
                {
                    "name": camera,
                    "match_type": "potential",
                    "verkada_model": match,
                }
            )
        return pd.Series(
            {
                "name": camera,
                "match_type": "unsupported",
                "verkada_model": None,
            }
        )

    if model_column is None:
        camera_column = identify_model_column_name(
            customer_list, verkada_cameras
        )
        log.info("Automatically identified Camera Column: '%s'", camera_column)
    else:
        camera_column = model_column
        log.info("Using specified Camera Column: '%s'", camera_column)

    # Handle both string and integer column identifiers with error checking
    if isinstance(camera_column, int):
        if camera_column < 0 or camera_column >= len(customer_list.columns):
            raise ValueError(
                f"Column index {camera_column} is out of bounds for DataFrame "
                f"with {len(customer_list.columns)} columns"
            )
        model_data = customer_list.iloc[:, camera_column]
    else:
        if camera_column not in customer_list.columns:
            raise KeyError(f"Column '{camera_column}' not found in DataFrame")
        model_data = customer_list[camera_column]
    verkada_cameras_list = get_camera_set(verkada_cameras)
    result = model_data.apply(match_camera)

    result = get_camera_count(customer_list, result)
    log.info("First 10 Matched Results: \n '%s'", result.head(10).to_string())

    # Define the order for sorting match types
    match_order = {
        "exact": 1,
        "identified": 2,
        "potential": 3,
        "unsupported": 4,
    }

    # Sort the results by match type using the defined order
    result["match_type_order"] = result["match_type"].map(match_order)
    sorted_result = result.sort_values(by="match_type_order").drop(
        columns=["match_type_order"]
    )

    return sorted_result


@time_function
def compile_camera_mp_channels(
    verkada_camera_list: List[CompatibleModel],
) -> List[CompatibleModel]:
    """Compile camera models.

    Args:
        verkada_camera_list (List[CompatibleModel]): The list of known cameras.

    Returns:
        pd.DataFrame: A DataFrame containing camera specifications for
        cameras with 5 megapixels or fewer.

    Raises:
        FileNotFoundError: If the "Camera Specs.csv" file does not exist.

    Examples:
        >>> low_mp_cameras = compile_low_mp_cameras()
        >>> print(low_mp_cameras.head())
            Manufacturer   Model Name   MP  Channels
        0             ACTi          A71  4.0       1.0
        1   Arecont Vision  AV02CID-200  2.1       1.0
        5   Arecont Vision     AV4656DN  4.0       3.0
        6   Arecont Vision     AV4956DN  4.0       2.0
        11        Avigilon   1.0-H3-DC1  1.0       1.0
    """

    camera_map = pd.read_csv("./Camera Specs.csv")
    # Iterate through each row in the DataFrame
    for _, row in camera_map.iterrows():
        model_name = row["Model Name"]
        mp = row["MP"]
        channels = row["Channels"]
        # Check if the name in the DataFrame matches any CompatibleModel
        for model in verkada_camera_list:
            if model.model_name.lower() == model_name.lower():
                # Update the channels based on the count
                model.channels += channels
                model.mp += mp
    return verkada_camera_list


def compile_low_mp_cameras() -> pd.DataFrame:
    """Compile a DataFrame of cameras with 5 megapixels or fewer.

    This function reads camera specifications from a CSV file and filters
    the data to return only those cameras that have a megapixel rating of
    5 or lower.

    Returns:
        pd.DataFrame: A DataFrame containing camera specifications for
        cameras with 5 megapixels or fewer.

    Raises:
        FileNotFoundError: If the "Camera Specs.csv" file does not exist.

    Examples:
        >>> low_mp_cameras = compile_low_mp_cameras()
        >>> print(low_mp_cameras.head())
            Manufacturer   Model Name   MP  Channels
        0             ACTi          A71  4.0       1.0
        1   Arecont Vision  AV02CID-200  2.1       1.0
        5   Arecont Vision     AV4656DN  4.0       3.0
        6   Arecont Vision     AV4956DN  4.0       2.0
        11        Avigilon   1.0-H3-DC1  1.0       1.0
    """

    camera_map = pd.read_csv("./Camera Specs.csv")
    return camera_map[camera_map["MP"] <= 5]


def compile_high_mp_cameras() -> pd.DataFrame:
    """Compile a DataFrame of cameras with more than 5 megapixels.

    This function reads camera specifications from a CSV file and filters
    the data to return only those cameras that have a megapixel rating of
    more than 5 megapixels.

    Returns:
        pd.DataFrame: A DataFrame containing camera specifications for
        cameras with more than 5 megapixels.

    Raises:
        FileNotFoundError: If the "Camera Specs.csv" file does not exist.

    Examples:
        >>> high_mp_cameras = compile_high_mp_cameras()
        >>> print(high_mp_cameras.head())
            Manufacturer Model Name    MP  Channels
        2  Arecont Vision  AV12176DN  12.0       5.0
        3  Arecont Vision  AV20175DN  20.0       5.0
        4  Arecont Vision  AV20275DN  20.0       4.0
        7  Arecont Vision   AV8185DN   8.0       5.0
        8             Ava   360-W-30  12.0       1.0
    """

    camera_map = pd.read_csv("./Camera Specs.csv")
    return camera_map[camera_map["MP"] > 5]


def count_low_mp_channels(customer_cameras: Dict[str, int]) -> int:
    """Calculate the total number of channels for low megapixel cameras.

    This function takes a dictionary of customer cameras and computes the total
    number of channels for those cameras that are classified as low megapixel.
    It merges the camera data with a predefined list of low megapixel cameras
    and calculates the total channels based on the count of each camera model.

    Args:
        customer_cameras (Dict[str, int]): A dictionary where keys are camera
        model names and values are the counts of each model.

    Returns:
        int: The total number of channels for low megapixel cameras.
    """
    cameras = pd.DataFrame(
        list(customer_cameras.items()), columns=["Model", "Count"]
    )  # Convert to DataFrame
    low_mp_list = compile_low_mp_cameras()
    merged_df = pd.merge(
        cameras, low_mp_list, left_on="Model", right_on="Model Name"
    )

    merged_df["Total Channels"] = merged_df["Count"] * merged_df["Channels"]
    log.debug("Low mp channels:\n%s", merged_df.head())

    return merged_df["Total Channels"].sum()


def count_high_mp_channels(customer_cameras: Dict[str, int]) -> int:
    """Calculate the total number of channels for high megapixel cameras.

    This function takes a dictionary of customer cameras and computes the
    total number of channels for those cameras that are classified as high
    megapixel. It merges the camera data with a predefined list of high
    megapixel cameras and calculates the total channels based on the count
    of each camera model.

    Args:
        customer_cameras (Dict[str, int]): A dictionary where keys are camera
        model names and values are the counts of each model.

    Returns:
        int: The total number of channels for high megapixel cameras.
    """

    cameras = pd.DataFrame(
        list(customer_cameras.items()), columns=["Model", "Count"]
    )  # Convert to DataFrame
    high_mp_list = compile_high_mp_cameras()
    merged_df = pd.merge(
        cameras, high_mp_list, left_on="Model", right_on="Model Name"
    )

    merged_df["Total Channels"] = merged_df["Count"] * merged_df["Channels"]
    log.debug("high mp channels:\n%s", merged_df.head())

    return merged_df["Total Channels"].sum()


def calculate_low_mp_storage(channels: int, retention: int) -> float:
    """
    Calculates the low megapixel storage requirement based on the number
    of channels and the retention period. The function returns the storage
    needed in gigabytes, depending on the specified retention duration.

    This function determines the storage requirement by applying different
    multipliers based on the retention period. It accounts for three
    retention ranges: up to 30 days, up to 60 days, and up to 90 days,
    returning a calculated storage value accordingly.

    Args:
        channels (int): The number of channels for which storage is being
            calculated.
        retention (int): The retention period in days.

    Returns:
        float: The calculated storage requirement in gigabytes, or None if
            the retention is not supported.
    """

    if retention <= 30:
        return channels * 0.256
    if retention <= 60:
        return channels * 0.512
    return channels * 0.768 if retention <= 90 else 0


def calculate_4k_storage(channels: int, retention: int) -> float:
    """
    Calculates the 4k storage requirement based on the number
    of channels and the retention period. The function returns the storage
    needed in terabytes, depending on the specified retention duration.

    This function determines the storage requirement by applying different
    multipliers based on the retention period. It accounts for three
    retention ranges: up to 30 days, up to 60 days, and up to 90 days,
    returning a calculated storage value accordingly.

    Args:
        channels (int): The number of channels for which storage is being
            calculated.
        retention (int): The retention period in days.

    Returns:
        float: The calculated storage requirement in gigabytes, or None if
            the retention value is not supported.
    """
    if retention <= 30:
        return channels * 0.512
    if retention <= 60:
        return channels * 1.024
    return channels * 2.048 if retention <= 90 else 0


def calculate_mp(width, height):
    """
    Calculates the megapixel (MP) value based on the given width and
    height in pixels. The function converts the pixel dimensions into
    megapixels by dividing the total pixel count by one million.

    This function is useful for determining the resolution of an image
    in terms of megapixels, which is a common metric in photography and
    imaging. It takes the width and height as inputs and returns the
    calculated MP value.

    Args:
        width (int): The width of the image in pixels.
        height (int): The height of the image in pixels.

    Returns:
        float: The calculated megapixel value.
    """
    log.info("%ix%i", width, height)
    return (width * height) / 1000000


def count_mp(
    camera_dataframe: pd.DataFrame, verkada_camera_list: List[CompatibleModel]
) -> List[int]:
    """Count the number of low and high channels required in a DataFrame.

    Args:
        camera_dataframe (pd.DataFrame): A DataFrame containing the camera models.
        verkada_camera_list (List[CompatibleModel]): A list of CompatibleModel

    Returns:
        List[int]: The number of low and high channels required.
    """
    low_count = 0
    high_count = 0

    # Iterate through each row in the DataFrame
    for _, row in camera_dataframe.iterrows():
        if row["verkada_model"] is not None:
            # Find the corresponding camera model in the list
            if camera_model := find_verkada_camera(
                str(row["verkada_model"]), verkada_camera_list
            ):
                # Assuming camera_model has an attribute 'mp' for megapixels
                if camera_model.mp <= 5:
                    low_count += int(row["count"])
                else:
                    high_count += int(row["count"])

    return [low_count, high_count]


@logging_decorator
def calculate_excess_channels(channels: int, connectors: List[Connector]):
    """
    Calculate the excess number of channels based on the provided
    connectors.

    This function sums the low channel capacities of the given connectors
    and determines how many channels exceed the specified number of
    channels. It is useful for assessing whether the available connectors
    meet or exceed the required channel capacity.

    Args:
        channels (int): The number of channels required.
        connectors (List[Connector]): A list of connectors with their low
            channel capacities.

    Returns:
        int: The excess number of channels, which is positive if there
            are more channels than required, or negative if there are
            not enough channels.
    """
    total_channels = sum(connector["low_channels"] for connector in connectors)
    return total_channels - channels
