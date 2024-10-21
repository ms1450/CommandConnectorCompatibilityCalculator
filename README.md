# Camera Model Comparison Script

## Overview

This script analyzes CSV files containing third-party camera models and compares them against our CSV of Command Connector-compatible models. It identifies camera model columns, finds exact matches, recognizes name variations, and suggests potential matches for similar models. After calculating the camera models, the script determines the required number of channels and calculates the most effective Command Connectors, along with their count, to meet the channel requirements.

### Features

- **Exact Match Detection**: Identifies camera models that match exactly with Command Connector-compatible models.
- **Identification of Similar Models**: Recognizes models even when their names are slightly different.
- **Potential Matches**: Suggests potential matches for models that are similar but not exact.
- **Recommend Command Connectors**: Recommends Command Connector based on identified cameras.

### Match Types

- **unsupported**: Camera was not found in Verkada Hardware Compatibility List
- **potential**: Camera model name closely resembles a model in Verkada Hardware Compatibility List
- **identified**: Camera model name partially contains an exact match from the Verkada Hardware Compatibility List
- **exact**: Camera model name is an exact match from the Verkada Hardware Compatibility List

## Purpose

The primary goal of this script is to provide a quick and accurate estimate of how many cameras in a given inventory would be supported by the Command Connector. It also identifies the best Command Connectors, and the 'Excess' channels based on the use case.

## Getting Started

1. Install all the required libraries using the requirements.txt: 
```pip install -r requirements.txt```
2. Update main.py line #87 with the filepath for the CSV
3. [Optional] Update main.py line #89 with the column for the Camera Model
4. Run main.py

## Testing and Contributions

To ensure the script's robustness and error handling capabilities, we need to test it against a diverse range of data. If you have any Excel or CSV files from customers listing their current camera models, please share them with us at <mehul.sen@verkada.com> for testing purposes.

Thank you!
