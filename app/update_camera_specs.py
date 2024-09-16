"""Module for downloading HCL files and updating specs."""

import os
import time
from typing import Optional

import pandas as pd
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait


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
        driver.get(url)
        button_xpath = ("//button[contains(@class, 'hidden') and contains(@class, 'md:block')]"
                        "//a[.//span[text()='CSV']]")
        download_button = WebDriverWait(driver, 20).until(
            EC.element_to_be_clickable((By.XPATH, button_xpath))
        )
        driver.execute_script("arguments[0].click();", download_button)

        # Wait for the file to be downloaded
        max_wait_time = 30
        start_time = time.time()
        while time.time() - start_time < max_wait_time:
            csv_files = [f for f in os.listdir(download_dir) if f.endswith(".csv")]
            if csv_files:
                print(f"CSV file downloaded successfully to {download_dir}!")
                return os.path.join(download_dir, csv_files[0])
            time.sleep(1)

        print("Error: CSV file download timed out.")
        return None


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

    downloaded_file = download_hcl(HCL_URL)
    if downloaded_file:
        update_specs(downloaded_file, SPECS_FILEPATH)
    else:
        print("Failed to download HCL file. Cannot update specs.")
