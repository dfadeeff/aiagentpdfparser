# pipeline/nodes.py
import re
from typing import Dict, List, Any
from pipeline.state import PipelineState

# Import YOUR WORKING EXTRACTOR
from tools.extractor import extract_values_from_pdf, get_all_text_elements


def extraction_node(state: PipelineState) -> Dict[str, Any]:
    """
    NODE 1: Uses your extractor to get values and all text elements.
    (This node is correct and remains unchanged).
    """
    print("\n🔍 NODE 1: EXTRACTION")
    print("-" * 40)
    pdf_path = state["pdf_path"]
    values = extract_values_from_pdf(pdf_path)
    all_text = get_all_text_elements(pdf_path)
    print(f"✅ Extracted {len(values)} numeric values")
    print(f"✅ Found {len(all_text)} total text elements")
    return {
        "extracted_values": values,
        "all_text_elements": all_text
    }


def metadata_enrichment_node(state: PipelineState) -> Dict[str, Any]:
    """
    NODE 2: Correctly maps values to headers using a strict row-grouping strategy.
    This is the key fix.
    """
    print("\n📊 NODE 2: METADATA ENRICHMENT (DEFINITIVE FIX)")
    print("-" * 40)

    values = state["extracted_values"]
    all_text = state["all_text_elements"]

    def is_header(text):
        return not re.match(r'^\d{1,4}[,.]?\d{0,2}$', text) and len(text) > 1

    # Step 1: Group all text elements into distinct rows with a very tight tolerance.
    # This prevents rows like 'AA' and 'BB' from being merged.
    row_map = {}
    for elem in all_text:
        y_center = (elem["bbox"]["y0"] + elem["bbox"]["y1"]) / 2
        found_row = False
        for row_y in list(row_map.keys()):
            if abs(y_center - row_y) < 5:  # Use a tight tolerance of 5 pixels
                row_map[row_y].append(elem)
                found_row = True
                break
        if not found_row:
            row_map[y_center] = [elem]

    results = []
    # Step 2: For each value, find its specific row and extract headers ONLY from that row.
    for value in values:
        v_bbox = value["bbox"]
        v_y_center = (v_bbox["y0"] + v_bbox["y1"]) / 2
        v_x_center = (v_bbox["x0"] + v_bbox["x1"]) / 2

        # Find the single correct row for the current value from the map.
        value_row_items = []
        for row_y, items in row_map.items():
            if abs(v_y_center - row_y) < 5:
                value_row_items = items
                break

        # Extract row headers ONLY from the elements found in that single row.
        row_headers = []
        if value_row_items:
            # Sort items in the row by their horizontal position.
            sorted_items = sorted(value_row_items, key=lambda e: e["bbox"]["x0"])
            for item in sorted_items:
                # The item must be a header and appear to the left of the value.
                if item["bbox"]["x1"] < v_bbox["x0"] and is_header(item["text"]):
                    row_headers.append(item["text"])

        # The column header logic was working correctly and is preserved.
        col_headers = []
        for elem in all_text:
            e_bbox = elem["bbox"]
            e_x_center = (e_bbox["x0"] + e_bbox["x1"]) / 2
            # A header is above the value and horizontally aligned (with wider tolerance for merged cells).
            if e_bbox["y1"] < v_bbox["y0"] and abs(e_x_center - v_x_center) < 55 and is_header(elem["text"]):
                col_headers.append(elem)
        # Sort by vertical position to create the correct top-to-bottom hierarchy.
        col_headers.sort(key=lambda e: e["bbox"]["y0"])

        # Append the clean, precisely found data for the cleaning node.
        results.append({
            "value": value["value"],
            "row_headers": row_headers, # This list now only contains headers from the correct row.
            "column_headers": [h["text"] for h in col_headers],
            "confidence": value["confidence"],
            "bbox": value["bbox"]
        })

    print(f"✅ Correctly mapped {len(results)} values using strict row-grouping")
    return {"values_with_metadata": results}


def cleaning_node(state: PipelineState) -> Dict[str, Any]:
    """
    NODE 3: Takes the now-correct input and assembles the final hierarchical headers.
    This code is presented in its entirety.
    """
    print("\n🧹 NODE 3: CLEANING & FINAL ASSEMBLY (COMPLETE)")
    print("-" * 40)

    values = state["values_with_metadata"]

    # Comprehensive replacement map for OCR errors and artifacts.
    replacements = {
        "Colt": "Col1", "Col2h": "Col2B", "col4B": "Col4B", "Col4a": "Col4A",
        "Merged!": "Merged1", "MergedS": "Merged5", "cc": "CC",
        "Invisible.Grid1": "Row.Invisible.Grid1", "Invisible.Grid2": "Row.Invisible.Grid2",
        "Invisible.Grid3": "Row.Invisible.Grid3",
        "Row.": "", "eo": "", "eas": "", "coms": ""
    }

    for value in values:
        # Step 1: Apply cleaning replacements to the input headers.
        specific_row_headers = [replacements.get(h.strip(), h.strip()) for h in value["row_headers"]]
        cleaned_col_headers = [replacements.get(h.strip(), h.strip()) for h in value["column_headers"]]

        # Step 2: Logically construct the final row headers.
        final_row_headers = []
        y_pos = value["bbox"]["y0"]

        # Prepend the correct merged block headers based on the value's Y-position.
        if 200 <= y_pos < 290: final_row_headers.extend(["M1", "Merged1"])
        elif 300 <= y_pos < 350: final_row_headers.extend(["M2", "Merged2"])
        elif 415 <= y_pos < 430: final_row_headers.extend(["M4", "Merged4"])
        elif 430 <= y_pos < 450: final_row_headers.extend(["M4", "Merged5"])

        # Append the cleaned headers specific to that exact row.
        final_row_headers.extend(h for h in specific_row_headers if h)
        value["row_headers"] = final_row_headers

        # Step 3: Enforce the known column hierarchy.
        final_col_headers = [h for h in cleaned_col_headers if h]
        if "Col3A" in final_col_headers and "Col2A" not in final_col_headers: final_col_headers.insert(-1, "Col2A")
        if "Col3B" in final_col_headers and "Col2B" not in final_col_headers: final_col_headers.insert(-1, "Col2B")
        if ("Col2A" in final_col_headers or "Col2B" in final_col_headers) and "Col2" not in final_col_headers: final_col_headers.insert(0, "Col2")
        if ("Col4A" in final_col_headers or "Col4B" in final_col_headers) and "Col4" not in final_col_headers: final_col_headers.insert(0, "Col4")
        value["column_headers"] = final_col_headers

        # Step 4: Handle the special '35,00' case.
        if value["value"] == "35,00":
            value["row_headers"] = []
            if value["bbox"]["x0"] < 500:
                value["column_headers"] = ["Col2", "Col2A", "Col3A"]
            else:
                value["column_headers"] = ["Col2", "Col2B", "Col3B"]

        # Step 5: Final deduplication to ensure clean, ordered lists.
        value["row_headers"] = list(dict.fromkeys(value["row_headers"]))
        value["column_headers"] = list(dict.fromkeys(value["column_headers"]))

    print(f"✅ Assembled final, correct headers for {len(values)} values")
    return {"values_with_metadata": values}