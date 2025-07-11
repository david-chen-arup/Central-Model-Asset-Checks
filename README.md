# Central-Model-Asset-Checks

## Overview

This repository contains scripts for generating input polyline CSV files required for GMA analysis. The scripts process a summary Excel file containing all polyline information and output the necessary CSV files for further analysis.

## Usage

1. Place the summary Excel file with polyline information in the appropriate directory.
2. Run the script from the `src` folder:
    ```bash
    cd src
    python gcreate_polyline_segment_csv_from_summary_xlsx.py
    ```
3. The generated CSV files will be available for use in GMA analysis.

## Folder Structure

- `src/` - Contains the script(s) for processing the summary Excel file and generating CSV files.
- `README.md` - Project documentation.

## Requirements

- Python 3.10
- Required Python packages (see `requirements.txt`)

## Purpose

Automate the creation of input polyline CSV files for GMA analysis based on a comprehensive summary Excel file.