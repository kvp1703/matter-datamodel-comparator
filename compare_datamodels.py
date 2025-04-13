# compare_datamodels.py
import json
import argparse
from copy import deepcopy
from collections import defaultdict
import logging # Use logging for info/errors

# Setup basic logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
log = logging.getLogger(__name__)

# --- Functions: parse_attribute_id, format_attribute_id, sort_value_if_list, preprocess_datamodel ---
# (Keep these functions as they were in the previous version)
def parse_attribute_id(attr_id_str):
    if isinstance(attr_id_str, int): return attr_id_str
    if isinstance(attr_id_str, str) and attr_id_str.startswith('0x'):
        cleaned_str = attr_id_str.replace('_', '')
        try: return int(cleaned_str, 16)
        except ValueError: return attr_id_str
    return attr_id_str

def format_attribute_id(attr_id_int):
    if isinstance(attr_id_int, int):
        hex_str = f"{attr_id_int:08X}"
        # Ensure minimum 4 digits after underscore if needed, pad if not
        prefix = hex_str[:4]
        suffix = hex_str[4:] if len(hex_str) > 4 else ""
        return f"0x{prefix}_{suffix}" # Handles IDs < 0xFFFF_FFFF
    return str(attr_id_int)

def sort_value_if_list(value):
    if isinstance(value, list):
        try:
            sorted_list = deepcopy(value)
            try:
                if all(isinstance(i, dict) for i in sorted_list) and sorted_list:
                     first_key = next(iter(sorted_list[0].keys()), None)
                     if first_key:
                         # Attempt to sort dicts by first key; requires comparable values
                         try:
                             sorted_list.sort(key=lambda x: x.get(first_key, None))
                         except TypeError: pass # Incomparable values, leave as is
                     # else: pass # Empty dicts, can't sort
                elif any(isinstance(i, dict) for i in sorted_list):
                     pass # Mixed list with dicts, too complex to reliably sort
                else:
                    # Handle None gracefully if sorting simple types
                     sorted_list.sort(key=lambda x: (x is None, x))
            except TypeError:
                 pass # Fallback for unorderable types
            return sorted_list
        except Exception:
            return value # Return original list if sorting fails
    return value

def preprocess_datamodel(filepath):
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            raw_data = json.load(f)
    except FileNotFoundError:
        log.error(f"File not found: {filepath}")
        return None
    except json.JSONDecodeError as e:
        log.error(f"Could not decode JSON from {filepath}: {e}")
        return None

    processed_data = defaultdict(lambda: defaultdict(dict))
    ignored_keys = {"Endpoint", "Cluster", "Attribute"}

    if not isinstance(raw_data, dict) or "datamodel" not in raw_data:
         log.error(f"Expected a dictionary with a 'datamodel' key in {filepath}")
         return None
    if not isinstance(raw_data["datamodel"], list):
        log.error(f"'datamodel' key should contain a list in {filepath}")
        return None

    for item in raw_data["datamodel"]:
        if not isinstance(item, dict): continue
        if "Endpoint" in item and "Cluster" in item and "Attribute" in item:
            endpoint = item["Endpoint"]
            cluster_raw = item["Cluster"]
            attribute_id_raw = item["Attribute"]
            # --- Store Cluster and Attribute IDs as Integers internally ---
            cluster_id = parse_attribute_id(cluster_raw)
            attribute_id = parse_attribute_id(attribute_id_raw)
            # --- End Change ---

            value = None
            value_found = False
            for key, val in item.items():
                if key not in ignored_keys:
                    value = sort_value_if_list(val)
                    value_found = True
                    break
            if value_found:
                processed_data[endpoint][cluster_id][attribute_id] = value
    return processed_data
# --- End of existing functions ---

# --- MODIFIED FUNCTION: diff_lists ---
def diff_lists(list1, list2):
    """
    Compares two lists (assumed sorted) and returns a dictionary:
    {'common': [], 'removed': [], 'added': []}
    Handles non-hashable items like dictionaries by comparing their JSON string representation.
    """
    diff_result = {'common': [], 'removed': [], 'added': []}
    i, j = 0, 0
    n1 = len(list1) if list1 else 0
    n2 = len(list2) if list2 else 0

    # Helper to get a comparable representation (JSON string for dicts/lists)
    def get_comparable(item):
        if isinstance(item, (dict, list)):
            try: return json.dumps(item, sort_keys=True)
            except TypeError: return repr(item)
        return item

    while i < n1 and j < n2:
        item1 = list1[i]
        item2 = list2[j]
        comp1 = get_comparable(item1)
        comp2 = get_comparable(item2)
        processed = False

        try:
            if comp1 == comp2:
                diff_result['common'].append(item1)
                i += 1
                j += 1
                processed = True
            # Basic comparison might fail for complex types, rely on string comparison
            elif comp1 < comp2:
                 diff_result['removed'].append(item1)
                 i += 1
                 processed = True
            else: # comp1 > comp2
                 diff_result['added'].append(item2)
                 j += 1
                 processed = True
        except TypeError:
            # Fallback if direct comparison fails even after string conversion attempt (should be rare)
            # Treat as difference and advance both (less accurate but prevents infinite loop)
            log.warning(f"Type error comparing list items: {type(item1)} vs {type(item2)}. Treating as different.")
            diff_result['removed'].append(item1)
            diff_result['added'].append(item2)
            i += 1
            j += 1
            processed = True # Mark as processed

        if not processed: # Should not happen with current logic, but as safety
             log.error("List diff comparison logic failed to advance.")
             i+=1; j+=1 # Force advance

    # Append remaining items
    while i < n1:
        diff_result['removed'].append(list1[i])
        i += 1
    while j < n2:
        diff_result['added'].append(list2[j])
        j += 1

    # Return None if no differences found, otherwise the dict
    if not diff_result['removed'] and not diff_result['added']:
        return None
    return diff_result
# --- END MODIFIED FUNCTION ---

def compare_datamodels(data1, data2):
    """
    Compares two preprocessed datamodels and returns differences.
    Includes detailed list diffs for modified list attributes.
    Uses integer IDs for clusters/attributes internally.
    """
    modified = defaultdict(lambda: defaultdict(dict))
    only_in_1 = defaultdict(lambda: defaultdict(dict))
    only_in_2 = defaultdict(lambda: defaultdict(dict))

    # Ensure endpoints are integers if possible, handle mixed types
    all_endpoints = sorted(list(set(data1.keys()) | set(data2.keys())))

    for endpoint in all_endpoints:
        # Use integer keys for clusters internally
        clusters1 = data1.get(endpoint, {})
        clusters2 = data2.get(endpoint, {})
        all_clusters = sorted(list(set(clusters1.keys()) | set(clusters2.keys())))

        for cluster_id in all_clusters:
            attributes1 = clusters1.get(cluster_id, {})
            attributes2 = clusters2.get(cluster_id, {})
            # Use integer keys for attributes internally
            all_attributes = sorted(list(set(attributes1.keys()) | set(attributes2.keys())))

            for attr_id in all_attributes:
                val1 = attributes1.get(attr_id)
                val2 = attributes2.get(attr_id)
                in1 = attr_id in attributes1
                in2 = attr_id in attributes2

                is_different = False
                list_diff_detail = None # Initialize list diff detail

                if in1 and in2:
                    comp1 = json.dumps(val1, sort_keys=True) if isinstance(val1, (dict, list)) else val1
                    comp2 = json.dumps(val2, sort_keys=True) if isinstance(val2, (dict, list)) else val2
                    if comp1 != comp2:
                        is_different = True
                        # Perform detailed list diff if both are lists
                        if isinstance(val1, list) and isinstance(val2, list):
                            list_diff_detail = diff_lists(val1, val2)
                elif in1 != in2: # One is present, the other is not
                    is_different = True # Implicitly different

                # Categorize
                if in1 and in2:
                    if is_different:
                        # Store old/new values and list diff detail if any
                        modified[endpoint][cluster_id][attr_id] = {
                            'old': val1,
                            'new': val2,
                            'list_diff': list_diff_detail # Will be None if not lists or lists are identical
                        }
                elif in1:
                    only_in_1[endpoint][cluster_id][attr_id] = val1
                elif in2:
                    only_in_2[endpoint][cluster_id][attr_id] = val2

    return dict(modified), dict(only_in_1), dict(only_in_2)


# --- Main guard (optional, for testing) ---
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Compare two Matter datamodel JSON files (internal use).')
    parser.add_argument('file1', help='Path to the first JSON datamodel file')
    parser.add_argument('file2', help='Path to the second JSON datamodel file')
    args = parser.parse_args()

    log.info("Preprocessing File 1...")
    dm1 = preprocess_datamodel(args.file1)
    log.info("Preprocessing File 2...")
    dm2 = preprocess_datamodel(args.file2)

    if dm1 is not None and dm2 is not None:
        log.info("Comparing...")
        mod, only1, only2 = compare_datamodels(dm1, dm2)
        print("\n--- Modified ---")
        print(json.dumps(mod, indent=2))
        print("\n--- Only in File 1 ---")
        print(json.dumps(only1, indent=2))
        print("\n--- Only in File 2 ---")
        print(json.dumps(only2, indent=2))
    else:
        log.error("Comparison failed due to preprocessing errors.")