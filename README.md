# Command Connector Compatibility Calculator Script

## Overview

A Python GUI application that helps users determine camera compatibility with command connectors and provides recommendations based on camera specifications.

### Features

- **Import Camera Lists**: Import camera lists from CSV files.
- **Compatibility Calculation**: Calculate compatibility with Verkada command connectors.
- **Recommendations**: Get recommendations for compatible connectors.
- **Detailed Info Panels**: View general info and camera details in a structured layout.
- **Export Functionality**: Export compatibility results to CSV files.
- **Customizable Settings**: Adjust appearance mode and other settings through the GUI.

### Requirements

- Python 3.12+
- tkinter
- pandas
- customtkinter
- nltk
- tabulate
- thefuzz

## Installation

1. Clone the repository:
```commandline
git clone https://github.com/ms1450/CommandConnectorCompatibilityCalculator.git
cd CommandConnectorCompatibilityCalculator
```
2. Install the required packages:
```commandline
pip install -r reqirements.txt
```

## Usage

1. Run the main application:
```commandline
python main.py
```

2. Use the GUI to import CSV camera lists, calculate compatibility, and view detailed information.
3. [Optional] Update the Command Connector Compatibility list by downloading the latest version from [here](https://www.verkada.com/security-cameras/command-connector/hcl/?page=1)

### GUI Overview
- Sidebar: Contains import button and tabs for Basic and Settings options.
  - Basic Tab: Import camera list files and view selected files.
  - Settings Tab: Adjust appearance mode and other settings.

- Main Window: Displays imported file name, export button, and compatibility results.
  - General Information: Displays file info, total cameras, and breakdown of matches.
  - Camera Details: Displays details for selected cameras.

## Purpose

The primary goal of this script is to provide a quick and accurate estimate of how many cameras in a given inventory would be supported by the Command Connector. It also identifies the best Command Connectors, and the 'Excess' channels based on the use case.

## License

This project is licensed under the MIT License. See the <ins>LICENSE</ins> file for more details.

## Authors
- Mehul Sen
- Ian Young

## Testing and Contributions

To ensure the script's robustness and error handling capabilities, we need to test it against a diverse range of data. If you have any Excel or CSV files from customers listing their current camera models, please share them with us at <mehul.sen@verkada.com> for testing purposes.

Thank you!
