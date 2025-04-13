# generate_html_report.py
import json
import argparse
import webbrowser
import os
import html
from collections import defaultdict
import logging # Use logging

# Setup basic logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
log = logging.getLogger(__name__)

# --- Try importing from the comparison script ---
try:
    # Assuming compare_datamodels.py is in the same directory or Python path
    from compare_datamodels import preprocess_datamodel, compare_datamodels, format_attribute_id
    log.info("Successfully imported functions from compare_datamodels.py")
except ImportError as e:
    log.error(f"Error importing from compare_datamodels.py: {e}")
    log.error("Please ensure 'compare_datamodels.py' is in the same directory or Python path.")
    exit(1)
# --- End Import ---


# --- SVG Icon Definition ---
# Simple right-pointing chevron SVG. Rotated via CSS.
# Using '1em' for width/height allows it to scale with font size.
# fill="currentColor" makes it inherit text color.
# style added for better default alignment.
SVG_ICON_HTML = '<svg class="chevron-icon" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 16 16" width="0.8em" height="0.8em" fill="currentColor" style="display: inline-block; vertical-align: -0.125em; transition: transform 0.2s ease-in-out;"><path fill-rule="evenodd" d="M4.646 1.646a.5.5 0 0 1 .708 0l6 6a.5.5 0 0 1 0 .708l-6 6a.5.5 0 0 1-.708-.708L10.293 8 4.646 2.354a.5.5 0 0 1 0-.708z"/></svg>'
# --- END SVG Icon Definition ---


# --- UPDATED: format_list_diff_html ---
def format_list_diff_html(list_diff_details):
    """Formats the list difference dictionary into a collapsible HTML <details> block using SVG icon."""
    if not list_diff_details:
        return ""

    removed_items = list_diff_details.get('removed', [])
    added_items = list_diff_details.get('added', [])

    if not removed_items and not added_items:
        return "" # No actual differences

    summary_text = "List Differences"

    details_content = ""
    if removed_items:
        items_html = "".join([f'<li class="removed-item"><span>{html.escape(json.dumps(item, ensure_ascii=False))}</span></li>' for item in removed_items])
        details_content += f'<div><strong>Only in Model 1:</strong><ul>{items_html}</ul></div>'
    if added_items:
        items_html = "".join([f'<li class="added-item"><span>{html.escape(json.dumps(item, ensure_ascii=False))}</span></li>' for item in added_items])
        details_content += f'<div><strong>Only in Model 2:</strong><ul>{items_html}</ul></div>'

    # Use the global SVG_ICON_HTML
    return f"""
<details class="list-diff-details">
    <summary><span class="toggle-icon">{SVG_ICON_HTML}</span>{summary_text}</summary>
    {details_content}
</details>
"""
# --- END UPDATED FUNCTION ---

import json
import html
from collections import defaultdict
import logging

# Assume SVG_ICON_HTML is defined globally or passed as an argument
# For completeness, let's define it here as it was in the previous step
SVG_ICON_HTML = '<svg class="chevron-icon" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 16 16" width="0.8em" height="0.8em" fill="currentColor" style="display: inline-block; vertical-align: -0.125em; transition: transform 0.2s ease-in-out;"><path fill-rule="evenodd" d="M4.646 1.646a.5.5 0 0 1 .708 0l6 6a.5.5 0 0 1 0 .708l-6 6a.5.5 0 0 1-.708-.708L10.293 8 4.646 2.354a.5.5 0 0 1 0-.708z"/></svg>'

# Assume format_attribute_id and format_list_diff_html are defined elsewhere
# Example dummy functions for testing:
def format_attribute_id(id_val):
    if isinstance(id_val, int):
        return f"0x{id_val:04X}"
    return str(id_val)

def format_list_diff_html(list_diff_details):
    """Dummy function - replace with your actual implementation"""
    if not list_diff_details: return ""
    removed = list_diff_details.get('removed', [])
    added = list_diff_details.get('added', [])
    if not removed and not added: return ""

    summary_text = "List Differences"
    details_content = ""
    if removed:
        items_html = "".join([f'<li class="removed-item"><span>{html.escape(json.dumps(item, ensure_ascii=False))}</span></li>' for item in removed])
        details_content += f'<div><strong>Only in Model 1:</strong><ul>{items_html}</ul></div>'
    if added:
        items_html = "".join([f'<li class="added-item"><span>{html.escape(json.dumps(item, ensure_ascii=False))}</span></li>' for item in added])
        details_content += f'<div><strong>Only in Model 2:</strong><ul>{items_html}</ul></div>'

    return f"""
<details class="list-diff-details">
    <summary><span class="toggle-icon">{SVG_ICON_HTML}</span>{summary_text}</summary>
    {details_content}
</details>
"""


log = logging.getLogger(__name__) # Assume logger is set up

# --- COMPLETE generate_html_diff FUNCTION (With Cluster Highlighting) ---
def generate_html_diff(data1, data2, modified, only_in_1, only_in_2, file1_name, file2_name):
    """Generates an HTML file with comparison, highlighting unique/modified attributes AND clusters."""

    # --- Attribute-level difference lookups (existing) ---
    modified_lookup = defaultdict(lambda: defaultdict(dict))
    for ep, clusters in modified.items():
        for cl, attrs in clusters.items():
            for attr, details in attrs.items():
                 modified_lookup[ep][cl][attr] = details

    only1_attr_set = set()
    for ep, clusters in only_in_1.items():
        for cl, attrs in clusters.items():
            for attr in attrs.keys():
                only1_attr_set.add((ep, cl, attr))

    only2_attr_set = set()
    for ep, clusters in only_in_2.items():
        for cl, attrs in clusters.items():
            for attr in attrs.keys():
                only2_attr_set.add((ep, cl, attr))

    # --- NEW: Pre-calculate Cluster-level differences ---
    clusters_only_in_1 = set()
    clusters_only_in_2 = set()
    all_endpoints = set(data1.keys()) | set(data2.keys())

    for ep in all_endpoints:
        clusters1 = set(data1.get(ep, {}).keys())
        clusters2 = set(data2.get(ep, {}).keys())

        for cl_id in clusters1 - clusters2:
            clusters_only_in_1.add((ep, cl_id))
        for cl_id in clusters2 - clusters1:
            clusters_only_in_2.add((ep, cl_id))
    # --- END NEW ---

    # --- Get all unique attribute keys (existing) ---
    all_keys_int = set()
    # Determine all EP/Cluster combinations present in either model to ensure headers are generated
    all_ep_cl_pairs = set()
    for ep, clusters in data1.items():
         all_ep_cl_pairs.update((ep, cl) for cl in clusters.keys())
         for cl, attrs in clusters.items():
            for attr in attrs.keys():
                all_keys_int.add((ep, cl, attr))
    for ep, clusters in data2.items():
         all_ep_cl_pairs.update((ep, cl) for cl in clusters.keys())
         for cl, attrs in clusters.items():
            for attr in attrs.keys():
                all_keys_int.add((ep, cl, attr))

    # Combine attribute keys and cluster pairs to ensure all headers/rows are considered
    # Create a representative key for sorting that includes dummy attr_id for clusters without attributes in the diff
    combined_keys_for_sorting = set(all_keys_int)
    for ep, cl_id in all_ep_cl_pairs:
        # Add a placeholder if this cluster isn't already represented by an attribute key
        # Using -1 or None as placeholder attr_id, ensuring it sorts first/last if needed, or just exists
        if not any(key[0] == ep and key[1] == cl_id for key in all_keys_int):
             combined_keys_for_sorting.add((ep, cl_id, None)) # Use None as placeholder


    # Sort: Endpoints, then Clusters, then Attributes (None sorts typically before ints)
    sorted_keys = sorted(list(combined_keys_for_sorting), key=lambda x: (x[0], x[1], x[2] if x[2] is not None else -1))

    # --- Start HTML Generation ---
    html_content = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Matter Data Model Comparison</title>
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
    <style>
        /* --- CSS Styles (Ensure ALL literal braces are doubled {{ }}) --- */
        :root {{
            /* CSS Variables */
            --font-primary: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, 'Open Sans', 'Helvetica Neue', sans-serif;
            --color-bg: #f8fafc;
            --color-text: #334155;
            --color-border: #e2e8f0;
            --color-endpoint-header: #e0e7ff;
            --color-cluster-header: #f1f5f9; /* Default cluster header bg */
            --color-attribute-header: #f8fafc;
            --color-modified-bg: #fffbeb; /* Attribute value highlight */
            --color-modified-border: #fcd34d; /* Yellow */
            --color-only1-bg: #fee2e2; /* Attribute value highlight */
            --color-only1-border: #fca5a5; /* Red */
            --color-only2-bg: #dcfce7; /* Attribute value highlight */
            --color-only2-border: #6ee7b7; /* Green */
            --color-na-text: #94a3b8;
            --color-icon: #64748b;
            --color-diff-added: #10b981;
            --color-diff-removed: var(--color-diff-added);
            --color-diff-removed-text: #065f46;
            --color-diff-added-text: #065f46;
            --border-diff-width: 5px;
        }}

        body {{ font-family: var(--font-primary); margin: 20px; background-color: var(--color-bg); color: var(--color-text); font-size: 14px; }}
        h1 {{ text-align: center; color: #1e293b; }}
        h2 {{ text-align: center; font-size: 1.2em; color: #475569; margin-bottom: 25px; font-weight: 500; }}
        .controls {{ text-align: center; margin-bottom: 25px; background-color: #fff; padding: 12px; border-radius: 6px; box-shadow: 0 1px 3px rgba(0,0,0,0.05); }}
        .controls button {{ padding: 9px 18px; margin: 0 8px; cursor: pointer; background-color: #6366f1; color: white; border: none; border-radius: 5px; font-size: 0.9em; font-weight: 500; transition: background-color 0.2s; }}
        .controls button:hover {{ background-color: #4f46e5; }}
        table {{ border-collapse: collapse; width: 100%; margin-top: 25px; border: 1px solid var(--color-border); table-layout: fixed; background-color: #fff; box-shadow: 0 4px 6px rgba(0,0,0,0.05); border-radius: 6px; overflow: hidden; }}
        th, td {{ border: 1px solid var(--color-border); padding: 10px 12px; text-align: left; vertical-align: top; word-wrap: break-word; }}
        th {{ background-color: #f1f5f9; font-weight: 600; position: sticky; top: 0; z-index: 1; font-size: 0.95em; color: #475569; }}

        .endpoint-header td, .cluster-header td, .attribute-row td {{ cursor: pointer; }}
        .endpoint-header td {{ background-color: var(--color-endpoint-header); font-weight: 600; }}
        .cluster-header td {{ background-color: var(--color-cluster-header); font-weight: 600; }}
        .attribute-row td:nth-child(3) {{ background-color: var(--color-attribute-header); font-weight: 500; font-family: monospace; vertical-align: middle; }}
        .attribute-row td.value-cell {{ vertical-align: top; }}

        /* Indentation and Borders for Hierarchy */
        .endpoint-header td:first-child,
        .cluster-header td:first-child,
        .attribute-row td:first-child {{ border-left: none; border-right: none; border-top: none; background-color: transparent !important; }}
        .cluster-header td:nth-child(2),
        .attribute-row td:nth-child(2) {{ border-left: none; border-right: none; border-top: none; background-color: transparent !important; }}
        .attribute-row td:nth-child(3) {{ border-left: none; border-right: none; border-top: none; }} /* Keep internal borders */

        /* Indentation Paddings */
        .cluster-header td:nth-child(2) {{ padding-left: 25px !important; }}
        .attribute-row td:nth-child(3) {{ padding-left: 45px !important; }}

        .na {{ color: var(--color-na-text); font-style: italic; }}
        .value-container {{ }}
        .value-container pre {{ white-space: pre-wrap; margin: 0; font-family: 'Menlo', 'Consolas', 'Courier New', monospace; font-size: 0.9em; background-color: #f8fafc; padding: 5px 8px; border: 1px solid #e2e8f0; border-radius: 4px; }}

        /* --- Attribute Row Highlighting (Values and Left Border) --- */
        .attribute-row.diff-value > td.value-cell {{ background-color: var(--color-modified-bg) !important; }}
        .attribute-row.only-model1 > td.value-cell {{ background-color: var(--color-only1-bg) !important; }}
        .attribute-row.only-model2 > td.value-cell {{ background-color: var(--color-only2-bg) !important; }}

        /* Attribute Row Left Border Indicators */
        .attribute-row.diff-value {{ border-left: var(--border-diff-width) solid var(--color-modified-border); }}
        .attribute-row.only-model1 {{ border-left: var(--border-diff-width) solid var(--color-only1-border); }}
        .attribute-row.only-model2 {{ border-left: var(--border-diff-width) solid var(--color-only2-border); }}

        /* --- NEW: Cluster Row Left Border Indicators --- */
        .cluster-header.only-model1 {{
            border-left: var(--border-diff-width) solid var(--color-only1-border);
            /* Optional: Slightly change background? Maybe too noisy. Border is clearer. */
            /* background-color: #fef3c7; */ /* Example slightly different shade */
        }}
        .cluster-header.only-model2 {{
            border-left: var(--border-diff-width) solid var(--color-only2-border);
             /* Optional: Slightly change background? */
            /* background-color: #ecfdf5; */ /* Example slightly different shade */
        }}
        /* --- END NEW --- */

        /* Ensure first N TDs of highlighted rows don't get highlight background/border */
        /* Attribute Row - First 3 TDs */
        .attribute-row.diff-value td:nth-child(-n+3),
        .attribute-row.only-model1 td:nth-child(-n+3),
        .attribute-row.only-model2 td:nth-child(-n+3) {{
             background-color: transparent !important;
             border-left-style: none !important;
             border-right-style: none !important;
        }}
        /* --- NEW: Cluster Row - First 2 TDs --- */
         .cluster-header.only-model1 td:nth-child(-n+2),
         .cluster-header.only-model2 td:nth-child(-n+2) {{
             background-color: transparent !important; /* Keep indent cells transparent */
             border-left-style: none !important; /* Prevent colored border on inner cells */
             border-right-style: none !important;
         }}
        /* --- END NEW --- */

         /* Restore internal separator between value cells */
         .attribute-row td.value-cell.value2 {{ border-left: 1px solid var(--color-border); }}
         /* Keep top border consistent */
         .attribute-row td:nth-child(-n+3) {{ border-top: 1px solid var(--color-border); }}
         .cluster-header td:nth-child(-n+2) {{ border-top: 1px solid var(--color-border); }} /* Ensure cluster top border stays consistent */


        .hidden {{ display: none; }}
        .toggle-icon {{ display: inline-flex; align-items: center; justify-content: center; width: 1.4em; height: 1.4em; margin-right: 6px; color: var(--color-icon); transition: transform 0.2s ease-in-out; vertical-align: middle; }}
        .toggle-icon .chevron-icon {{ }}

        /* Toggle Icon Rotation */
        .collapsible[data-state="collapsed"] > td > .toggle-icon,
        .collapsible[data-state="collapsed"] > td:nth-child(2) > .toggle-icon,
        .collapsible[data-state="collapsed"] > td:nth-child(3) > .toggle-icon {{ transform: rotate(0deg); }}
        .collapsible[data-state="expanded"] > td > .toggle-icon,
        .collapsible[data-state="expanded"] > td:nth-child(2) > .toggle-icon,
        .collapsible[data-state="expanded"] > td:nth-child(3) > .toggle-icon {{ transform: rotate(90deg); }}

        /* List Diff <details> Styling */
        details.list-diff-details {{ font-size: 0.9em; margin-top: 8px; background-color: #f1f5f9; border: 1px solid #e2e8f0; border-radius: 4px; padding: 0; overflow: hidden; }}
        details.list-diff-details summary {{ padding: 5px 10px; cursor: pointer; font-weight: 500; background-color: #e2e8f0; list-style: none; position: relative; color: var(--color-text); }}
        details.list-diff-details summary::-webkit-details-marker {{ display: none; }}
        details.list-diff-details summary .toggle-icon {{ width: 1em; height: 1em; margin-right: 5px; transform: rotate(0deg); }}
        details.list-diff-details[open] > summary .toggle-icon {{ transform: rotate(90deg); }}
        details.list-diff-details div {{ padding: 8px 10px 10px 15px; }}
        details.list-diff-details ul {{ list-style: none; padding-left: 15px; margin: 5px 0 0 0; }}
        details.list-diff-details li {{ margin-bottom: 4px; }}
        details.list-diff-details span {{ font-family: 'Menlo', 'Consolas', monospace; background-color: #fff; padding: 2px 5px; border-radius: 3px; border: 1px solid #e2e8f0; display: inline-block; }}
        .list-diff-details .removed-item span {{ border-left: 2px solid var(--color-diff-removed); color: var(--color-diff-removed-text); background-color: #d1fae5; }}
        .list-diff-details .added-item span {{ border-left: 2px solid var(--color-diff-added); color: var(--color-diff-added-text); background-color: #d1fae5; }}

        /* Legend Styling */
        .legend {{ border-top: 2px solid var(--color-border); padding-top: 20px; }}
        .legend ul {{ list-style: none; padding-left: 0; font-size: 0.95em; }}
        .legend li {{ margin-bottom: 8px; display: flex; align-items: center; }}
        .legend .color-box {{ display: inline-block; width: 18px; height: 18px; margin-right: 10px; border: 1px solid #cbd5e1; vertical-align: middle; border-radius: 3px; flex-shrink: 0; }}
        .legend .na-box {{ font-style: italic; color: var(--color-na-text); margin-right: 10px; width: 18px; text-align: center; display: inline-block; flex-shrink: 0; }}
        .legend details.list-diff-details {{ display: inline-block; width: auto; padding: 1px; vertical-align: middle; margin: 0 5px 0 0; }}
        .legend details.list-diff-details summary {{ padding: 1px 5px; display: inline-block; font-weight: normal; background-color: #e2e8f0; }}
        .legend .list-diff-text {{ display: inline; }}
        .legend .legend-toggle-icon {{ display: inline-flex; align-items: center; justify-content: center; width: 1.2em; height: 1.2em; color: var(--color-icon); vertical-align: middle; }}
    </style>
</head>
<body>
    <h1>Matter Data Model Comparison</h1>
    <h2>{html.escape(file1_name)}   |   {html.escape(file2_name)}</h2>

    <div class="controls">
        <button id="expand-all">Expand All</button>
        <button id="collapse-all">Collapse All</button>
    </div>

    <table>
        <thead>
            <tr>
                <th style="width: 5%;"></th> <!-- EP indent -->
                <th style="width: 15%;">Cluster</th>
                <th style="width: 20%;">Attribute</th>
                <th style="width: 30%;">Model 1 Value</th>
                <th style="width: 30%;">Model 2 Value</th>
            </tr>
        </thead>
        <tbody id="comparison-body">
    """ # End of initial HTML string

    last_ep = -1
    last_cl_id = -1
    initial_ep_state = 'collapsed'
    initial_cl_state = 'collapsed'
    initial_attr_state = 'collapsed'

    if not sorted_keys: # Check the combined list
         html_content += '<tr><td colspan="5" style="text-align:center; font-style:italic;">No endpoints or clusters found in either model.</td></tr>'

    # --- Loop through combined keys (includes attributes and cluster placeholders) ---
    for ep, cl_id, attr_id_or_none in sorted_keys:

        # --- Endpoint Header ---
        if ep != last_ep:
            html_content += f'<tr class="endpoint-header collapsible" data-ep="{ep}" data-state="{initial_ep_state}" title="Click to toggle Endpoint {ep} details">\n'
            html_content += f'<td colspan="5"><span class="toggle-icon">{SVG_ICON_HTML}</span>Endpoint {ep}</td>\n'
            html_content += f'</tr>\n'
            last_ep = ep
            last_cl_id = -1 # Reset cluster tracking for new EP

        # --- Cluster Header ---
        # Check if we need to draw a cluster header (new cluster ID for this endpoint)
        if cl_id != last_cl_id:
             hidden_class_cl = 'hidden' if initial_ep_state == 'collapsed' else ''
             cluster_display_id = format_attribute_id(cl_id)

             # --- NEW: Determine cluster row class ---
             cluster_row_class = ""
             if (ep, cl_id) in clusters_only_in_1:
                 cluster_row_class = "only-model1"
             elif (ep, cl_id) in clusters_only_in_2:
                 cluster_row_class = "only-model2"
             # --- END NEW ---

             # Add the class to the cluster row
             html_content += f'<tr class="cluster-header collapsible cluster-ep-{ep} {hidden_class_cl} {cluster_row_class}" data-ep="{ep}" data-cl="{cl_id}" data-state="{initial_cl_state}" title="Click to toggle Cluster {cluster_display_id} details">\n'
             html_content += f'<td style="border: none;"></td>\n' # EP indent
             html_content += f'<td colspan="4"><span class="toggle-icon">{SVG_ICON_HTML}</span>Cluster {cluster_display_id}</td>\n'
             html_content += f'</tr>\n'
             last_cl_id = cl_id

        # --- Attribute Row (Merged Header and Content) ---
        # Only draw attribute rows if attr_id_or_none is not the placeholder (None)
        if attr_id_or_none is not None:
            attr_id = attr_id_or_none # Use the actual attribute ID
            hidden_class_attr = 'hidden' if initial_ep_state == 'collapsed' or initial_cl_state == 'collapsed' else ''
            attr_display_id = format_attribute_id(attr_id)

            val1 = data1.get(ep, {}).get(cl_id, {}).get(attr_id)
            val2 = data2.get(ep, {}).get(cl_id, {}).get(attr_id)

            row_key = (ep, cl_id, attr_id)
            attr_row_class = "" # Highlighting class for the attribute row
            list_diff_html = ""
            list_diff_details = None

            if row_key in only1_attr_set: # Use the attribute-specific set
                attr_row_class = "only-model1"
            elif row_key in only2_attr_set: # Use the attribute-specific set
                attr_row_class = "only-model2"
            elif ep in modified_lookup and cl_id in modified_lookup[ep] and attr_id in modified_lookup[ep][cl_id]:
                attr_row_class = "diff-value"
                list_diff_details = modified_lookup[ep][cl_id][attr_id].get('list_diff')
                if list_diff_details:
                    list_diff_html = format_list_diff_html(list_diff_details)

            # Prepare value strings and N/A state
            has_val1 = val1 is not None
            has_val2 = val2 is not None
            val1_str = json.dumps(val1, indent=2, ensure_ascii=False) if has_val1 else ""
            val2_str = json.dumps(val2, indent=2, ensure_ascii=False) if has_val2 else ""

            val1_container_content = f"<pre>{html.escape(val1_str)}</pre>{list_diff_html}" if has_val1 else ""
            val1_container_html = f'<div class="value-container hidden">{val1_container_content}</div>'
            na1_html = f'<div class="value-container hidden"><span class="na">N/A</span></div>'

            val2_container_content = f"<pre>{html.escape(val2_str)}</pre>" if has_val2 else ""
            val2_container_html = f'<div class="value-container hidden">{val2_container_content}</div>'
            na2_html = f'<div class="value-container hidden"><span class="na">N/A</span></div>'

            # Add the specific attribute class to the attribute row
            html_content += f"""
                <tr class="attribute-row collapsible attribute-ep-{ep} attribute-cl-{ep}-{cl_id} {attr_row_class} {hidden_class_attr}"
                    data-ep="{ep}" data-cl="{cl_id}" data-attr="{attr_id}" data-state="{initial_attr_state}"
                    title="Click to toggle Attribute {attr_display_id} details">
                    <td style="border: none;"></td> <!-- EP indent -->
                    <td style="border: none;"></td> <!-- Cluster indent -->
                    <td><span class="toggle-icon">{SVG_ICON_HTML}</span>{attr_display_id}</td> <!-- Attribute ID -->
                    <td class="value-cell value1" data-has-value="{str(has_val1).lower()}">
                        {val1_container_html if has_val1 else na1_html}
                    </td> <!-- Model 1 Value -->
                    <td class="value-cell value2" data-has-value="{str(has_val2).lower()}">
                        {val2_container_html if has_val2 else na2_html}
                    </td> <!-- Model 2 Value -->
                </tr>
            """

    # --- Finish HTML ---
    legend_toggle_icon_expanded = f'<span class="legend-toggle-icon" style="transform: rotate(90deg);">{SVG_ICON_HTML}</span>'
    legend_toggle_icon_collapsed = f'<span class="legend-toggle-icon">{SVG_ICON_HTML}</span>'
    legend_toggle_text = f"{legend_toggle_icon_expanded} / {legend_toggle_icon_collapsed} Click Endpoint/Cluster/Attribute headers to collapse/expand sections."
    list_diff_legend_icon = f'<details class="list-diff-details" style="display: inline-block; width: auto; padding: 1px; vertical-align: middle; margin-right: 5px;"><summary style="padding: 1px 5px; display: inline-block; font-weight: normal; background-color: #e2e8f0;"><span class="toggle-icon">{SVG_ICON_HTML}</span>List Differences</summary></details>'

    html_content += f"""
        </tbody>
    </table>

    <div class="legend" style="margin-top: 30px;">
        <strong>Legend:</strong>
        <ul>
            <!-- Cluster Level -->
            <li><span class="color-box" style="background-color: var(--color-cluster-header); border-left: var(--border-diff-width) solid var(--color-only1-border);"></span> Cluster present only in Model 1 (header row has red left strip).</li>
            <li><span class="color-box" style="background-color: var(--color-cluster-header); border-left: var(--border-diff-width) solid var(--color-only2-border);"></span> Cluster present only in Model 2 (header row has green left strip).</li>
            <!-- Attribute Level -->
            <li><span class="color-box" style="background-color: var(--color-modified-bg); border-left: var(--border-diff-width) solid var(--color-modified-border);"></span> Attribute values differ between models (attribute row has yellow left strip, values highlighted).</li>
            <li><span class="color-box" style="background-color: var(--color-only1-bg); border-left: var(--border-diff-width) solid var(--color-only1-border);"></span> Attribute present only in Model 1 (attribute row has red left strip, value highlighted).</li>
            <li><span class="color-box" style="background-color: var(--color-only2-bg); border-left: var(--border-diff-width) solid var(--color-only2-border);"></span> Attribute present only in Model 2 (attribute row has green left strip, value highlighted).</li>
            <!-- General -->
            <li><span class="na-box">N/A</span> Attribute not present in the corresponding model.</li>
            <li>{legend_toggle_text}</li>
            <li>{list_diff_legend_icon}<span class="list-diff-text">Details shown when list contents differ.</span></li>
            <li><span style="color: var(--color-diff-removed-text); background-color: #d1fae5; padding: 0 3px; border-left: 2px solid var(--color-diff-removed);">Item Text</span> Item present only in Model 1 or Model 2 (within List Differences detail).</li>
        </ul>
    </div>

     <!-- JAVASCRIPT (Ensure f-string escaping {{ }}) -->
    <script>
    document.addEventListener('DOMContentLoaded', function() {{
        const comparisonBody = document.getElementById('comparison-body');
        const expandAllBtn = document.getElementById('expand-all');
        const collapseAllBtn = document.getElementById('collapse-all');

        function setToggleState(element, expand) {{
            if (!element || !element.classList.contains('collapsible')) return;
            element.dataset.state = expand ? 'expanded' : 'collapsed';
        }}

        function toggleAttributeValueVisibility(attrRow, expand) {{
            if (!attrRow || !attrRow.classList.contains('attribute-row')) return;
            attrRow.querySelectorAll('.value-cell').forEach(cell => {{
                const valueContainer = cell.querySelector('.value-container');
                if (valueContainer) {{
                    valueContainer.classList.toggle('hidden', !expand);
                }}
            }});
        }}

        comparisonBody.addEventListener('click', function(event) {{
            const listDiffSummary = event.target.closest('details.list-diff-details > summary');
            if (listDiffSummary) {{ return; }}

            const headerRow = event.target.closest('tr.collapsible');
            if (!headerRow) return;

            const ep = headerRow.dataset.ep;
            const cl_id = headerRow.dataset.cl;
            const attr_id = headerRow.dataset.attr; // Will be undefined for cluster/endpoint rows
            const isExpanding = headerRow.dataset.state === 'collapsed';

            setToggleState(headerRow, isExpanding);

            if (attr_id !== undefined) {{ // Check if it's an attribute row click
                toggleAttributeValueVisibility(headerRow, isExpanding);
            }} else if (cl_id !== undefined) {{ // Check if it's a cluster row click
                const childAttrRows = comparisonBody.querySelectorAll(`.attribute-row.attribute-cl-${{ep}}-${{cl_id}}`);
                childAttrRows.forEach(attrRow => {{
                    attrRow.classList.toggle('hidden', !isExpanding);
                    setToggleState(attrRow, isExpanding); // Expand/collapse attributes with cluster
                    toggleAttributeValueVisibility(attrRow, isExpanding);
                }});
            }} else {{ // Endpoint row click
                const childClusterHeaders = comparisonBody.querySelectorAll(`.cluster-header.cluster-ep-${{ep}}`);
                const childAttrRows = comparisonBody.querySelectorAll(`.attribute-row.attribute-ep-${{ep}}`);

                childClusterHeaders.forEach(clusterRow => {{
                    clusterRow.classList.toggle('hidden', !isExpanding);
                    setToggleState(clusterRow, isExpanding); // Expand/collapse clusters with endpoint
                }});

                childAttrRows.forEach(attrRow => {{
                    attrRow.classList.toggle('hidden', !isExpanding);
                    if (isExpanding) {{
                        setToggleState(attrRow, true);
                        toggleAttributeValueVisibility(attrRow, true);
                    }} else {{
                         setToggleState(attrRow, false);
                         toggleAttributeValueVisibility(attrRow, false);
                    }}
                }});
            }}
        }});

        function setAllSections(expand) {{
            const allCollapsibleHeaders = comparisonBody.querySelectorAll('.collapsible');
            const allClusterRows = comparisonBody.querySelectorAll('.cluster-header');
            const allAttrRows = comparisonBody.querySelectorAll('.attribute-row');

            allCollapsibleHeaders.forEach(header => {{ setToggleState(header, expand); }});
            allClusterRows.forEach(row => {{ row.classList.toggle('hidden', !expand); }});
            allAttrRows.forEach(row => {{
                 row.classList.toggle('hidden', !expand);
                 toggleAttributeValueVisibility(row, expand);
            }});
        }}

        expandAllBtn.addEventListener('click', () => setAllSections(true));
        collapseAllBtn.addEventListener('click', () => setAllSections(false));
        setAllSections(false); // Initial state
    }});
    </script>

</body>
</html>
    """ # End of HTML string

    return html_content
# --- END OF FUNCTION ---
# --- Main function (Unchanged) ---
def main():
    parser = argparse.ArgumentParser(description='Compare two Matter datamodel JSON files and generate an enhanced HTML table report.')
    parser.add_argument('file1', help='Path to the first JSON datamodel file')
    parser.add_argument('file2', help='Path to the second JSON datamodel file')
    parser.add_argument('-o', '--output', default='datamodel_comparison_enhanced.html',
                        help='Output HTML file name (default: datamodel_comparison_enhanced.html)')
    args = parser.parse_args()

    log.info(f"Processing Datamodel 1: {args.file1}")
    datamodel1 = preprocess_datamodel(args.file1)
    if datamodel1 is None: return

    log.info(f"Processing Datamodel 2: {args.file2}")
    datamodel2 = preprocess_datamodel(args.file2)
    if datamodel2 is None: return

    log.info("Comparing datamodels...")
    modified, only_in_1, only_in_2 = compare_datamodels(datamodel1, datamodel2)

    log.info("Generating HTML report...")
    html_report = generate_html_diff(datamodel1, datamodel2, modified, only_in_1, only_in_2, args.file1, args.file2)

    try:
        output_filename = args.output
        with open(output_filename, 'w', encoding='utf-8') as f:
            f.write(html_report)
        log.info(f"Successfully generated HTML report: {output_filename}")

        try:
            webbrowser.open('file://' + os.path.realpath(output_filename))
        except Exception as e:
            log.warning(f"Could not automatically open the report in a browser: {e}")
            log.info(f"Please open the file manually: {os.path.realpath(output_filename)}")

    except IOError as e:
        log.error(f"Error writing HTML file: {e}")
    except Exception as e:
        log.error(f"Unexpected error during HTML generation or writing: {e}", exc_info=True)


if __name__ == "__main__":
    main()