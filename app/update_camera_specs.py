"""Module for downloading HCL files and updating specs."""

# pylint: disable=ungrouped-imports

import os
import time
from subprocess import check_call
from sys import executable
from typing import Optional

try:
    import pandas as pd
    from selenium import webdriver
    from selenium.webdriver.chrome.options import Options
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support import expected_conditions as EC
    from selenium.webdriver.support.ui import WebDriverWait
except ImportError as e:
    package_name = str(e).split()[-1]
    check_call([executable, "-m", "pip", "install", package_name])
    # Import again after installation
    import pandas as pd
    from selenium import webdriver
    from selenium.webdriver.chrome.options import Options
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support import expected_conditions as EC
    from selenium.webdriver.support.ui import WebDriverWait

from app import logging_decorator, time_function


@time_function
def download_hcl(url: str) -> Optional[str]:
    """
    Download HCL file from the given URL.

    Args:
        url (str): The URL to download the HCL file from.

    Returns:
        Optional[str]: The path to the downloaded file, or None if download failed.
    """
    download_dir = os.path.abspath(os.path.join(os.getcwd(), ".."))

    chrome_options = Options()
    chrome_options.add_experimental_option(
        "prefs",
        {
            "download.default_directory": download_dir,
            "download.prompt_for_download": False,
            "download.directory_upgrade": True,
        },
    )
    chrome_options.add_argument("--headless")  # Run in headless mode

    with webdriver.Chrome(options=chrome_options) as driver:
        return download_csv(driver, url, download_dir)


@time_function
def download_csv(driver, url, download_dir):
    """Downloads a CSV file from a specified URL using a web driver.

    This function navigates to the provided URL, locates the download
    button for a CSV file, and initiates the download. It waits for the
    file to be downloaded within a specified time frame and returns the
    path to the downloaded file if successful.

    Args:
        driver: The web driver used to interact with the web page.
        url (str): The URL from which to download the CSV file.
        download_dir (str): The directory where the CSV file will be
            downloaded.

    Returns:
        str: The path to the downloaded CSV file if successful, otherwise
            None.
    """
    driver.get(url)
    button_xpath = (
        "//button[contains(@class, 'hidden') and contains(@class, 'md:block')]"
        "//a[.//span[text()='CSV']]"
    )
    download_button = WebDriverWait(driver, 20).until(
        EC.element_to_be_clickable((By.XPATH, button_xpath))
    )
    driver.execute_script("arguments[0].click();", download_button)

    # Wait for the file to be downloaded
    max_wait_time = 30
    start_time = time.time()
    while time.time() - start_time < max_wait_time:
        if csv_files := [
            f for f in os.listdir(download_dir) if f.endswith(".csv")
        ]:
            print(f"CSV file downloaded successfully to {download_dir}!")
            return os.path.join(download_dir, csv_files[0])
        time.sleep(1)

    print("Error: CSV file download timed out.")
    return None


@logging_decorator
def update_specs(hcl_file: str, specs_file: str) -> None:
    """
    Update specs by comparing HCL and specs files.

    Args:
        hcl_file (str): Path to the HCL file.
        specs_file (str): Path to the specs file.
    """
    # Reading the CSV files
    df_hcl = pd.read_csv(hcl_file, skiprows=4, encoding="UTF-8")
    df_specs = pd.read_csv(specs_file, header=0, encoding="UTF-8")

    # Extracting the 'Model Name' columns
    set_hcl = set(df_hcl["Model Name"])
    set_specs = set(df_specs["Model Name"])



    # Finding entries in set_hcl that are not in set_specs
    missing_in_specs = set_hcl - set_specs

    # Printing each missing entry with all its fields
    for entry in missing_in_specs:
        # Get the full row for the missing entry
        row = df_hcl[df_hcl["Model Name"] == entry].iloc[0]
        print(f"Missing entry: {entry}")
        print("Full details:")
        for column, value in row.items():
            print(f"  {column}: {value}")
        print("------------------------")


if __name__ == "__main__":
    HCL_URL = "https://www.verkada.com/security-cameras/command-connector/hcl/?page=1"
    HCL_FILEPATH = "../Verkada Command Connector Compatibility.csv"
    SPECS_FILEPATH = "../Camera Specs.csv"
    update_specs(HCL_FILEPATH, SPECS_FILEPATH)

#    if downloaded_file := download_hcl(HCL_URL):
#        update_specs(downloaded_file, SPECS_FILEPATH)
#    else:
#        print("Failed to download HCL file. Cannot update specs.")
