# ESP-Matter Datamodel Comparison Tool

## Overview

This tool consists of two Python scripts designed to compare two ESP-Matter datamodel JSON files. It identifies differences between the data models (provided in json format) and generates an interactive HTML report to visualize these changes clearly.

This is particularly useful for:

*   Tracking configuration changes between different firmware versions.
*   Comparing default datamodels with customized ones.
*   Debugging datamodel inconsistencies.

## Features

*   Compares two Matter datamodel JSON files attribute by attribute.
*   Identifies attributes that are:
    *   **Modified:** Present in both files but with different values.
    *   **Only in Model 1:** Present only in the first file.
    *   **Only in Model 2:** Present only in the second file.
*   Provides detailed comparison for list-type attributes, showing added and removed items.
*   Generates a well-formatted, interactive HTML report.
*   **Interactive HTML Report Features:**
    *   Hierarchical view (Endpoint -> Cluster -> Attribute).
    *   Collapsible/Expandable sections for Endpoints, Clusters, and Attribute values.
    *   "Expand All" / "Collapse All" buttons for easy navigation.
    *   Color-coded highlighting in the report:
        *   **Yellow Background (Value Cells):** Attribute values differ between models.
        *   **Red Background (Value Cells) / Red Left Border (Row):** Attribute present only in Model 1.
        *   **Green Background (Value Cells) / Green Right Border (Row):** Attribute present only in Model 2.
    *   Clear indication (`N/A`) for attributes missing in one model.
    *   Sticky `<thead>`, Endpoint, and Cluster headers for persistent context while scrolling.
    *   Modern chevron icons for collapse/expand toggles.
    *   Detailed legend explaining the highlighting and symbols.

## Files

1.  `compare_datamodels.py`:
    *   Contains the core logic for parsing, preprocessing, and comparing the datamodel JSON files.
    *   Handles conversion of hex IDs and sorting/comparison of list values.
    *   Provides functions used by the HTML generation script.
    *   *Generally not intended to be run directly by the user.*
2.  `generate_html_report.py`:
    *   The main script to be executed by the user.
    *   Imports comparison functions from `compare_datamodels.py`.
    *   Takes two JSON file paths as input.
    *   Generates the final `datamodel_comparison_enhanced.html` report (or a custom name).
    *   Automatically attempts to open the generated report in the default web browser.

## Prerequisites

*   Python 3.x

## Usage

The primary way to use the tool is by running the `generate_html_report.py` script from your terminal.

**Command:**

```bash
python generate_html_report.py base_config.json custom_config.json -o dm_diff.html
