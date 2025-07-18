# pipeline/nodes.py
import re
from typing import Dict, List, Any
from pipeline.state import PipelineState

# Import YOUR WORKING EXTRACTOR
from tools.extractor import extract_values_from_pdf, get_all_text_elements


def extraction_node(state: PipelineState) -> Dict[str, Any]:
    """
    NODE 1: Uses your extractor to get values and all text elements.
    """
    print("\n🔍 NODE 1: EXTRACTION")
    print("-" * 40)

    pdf_path = state["pdf_path"]

    # Use YOUR extractor functions
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
    NODE 2: Adds row and column headers to each value.
    """
    print("\n📊 NODE 2: METADATA ENRICHMENT")
    print("-" * 40)

    values = state["extracted_values"]
    all_text = state["all_text_elements"]

    # Helper to check if text is a header (not numeric)
    def is_header(text):
        return not re.match(r'^\d{1,4}[,.]?\d{0,2}$', text)

    results = []

    for value in values:
        v_bbox = value["bbox"]
        v_x_center = (v_bbox["x0"] + v_bbox["x1"]) / 2
        v_y_center = (v_bbox["y0"] + v_bbox["y1"]) / 2

        # Find row headers (text to the left of value)
        row_headers = []
        for elem in all_text:
            e_bbox = elem["bbox"]
            e_text = elem["text"]

            # Is it a header, to the left, and on same row?
            if (is_header(e_text) and
                    e_bbox["x1"] < v_bbox["x0"] and
                    abs((e_bbox["y0"] + e_bbox["y1"]) / 2 - v_y_center) < 15):
                row_headers.append({
                    "text": e_text,
                    "x": e_bbox["x0"]
                })

        # Sort by x position
        row_headers.sort(key=lambda h: h["x"])
        row_header_texts = [h["text"] for h in row_headers]

        # Find column headers (text above value)
        col_headers = []
        for elem in all_text:
            e_bbox = elem["bbox"]
            e_text = elem["text"]

            # Is it a header, above, and in same column?
            if (is_header(e_text) and
                    e_bbox["y1"] < v_bbox["y0"] and
                    abs((e_bbox["x0"] + e_bbox["x1"]) / 2 - v_x_center) < 50):
                col_headers.append({
                    "text": e_text,
                    "y": e_bbox["y0"]
                })

        # Sort by y position
        col_headers.sort(key=lambda h: h["y"])
        col_header_texts = [h["text"] for h in col_headers]

        # Build result
        results.append({
            "value": value["value"],
            "row_headers": row_header_texts,
            "column_headers": col_header_texts,
            "confidence": value["confidence"],
            "bbox": value["bbox"]
        })

    print(f"✅ Added metadata to {len(results)} values")

    return {"values_with_metadata": results}


def cleaning_node(state: PipelineState) -> Dict[str, Any]:
    """
    NODE 3: Cleans up OCR errors in headers.
    """
    print("\n🧹 NODE 3: CLEANING")
    print("-" * 40)

    values = state["values_with_metadata"]

    # Common OCR errors to fix
    replacements = {
        "Colt": "Col1",
        "MergedS": "Merged5",
        "Merged!": "Merged1",
        "col4B": "Col4B",
        "Col2h": "Col2B",
        "InvisibleGrid": "Invisible.Grid"
    }

    for value in values:
        # Clean row headers
        cleaned_row = []
        for header in value["row_headers"]:
            cleaned = header
            for old, new in replacements.items():
                cleaned = cleaned.replace(old, new)
            if cleaned not in cleaned_row:  # Remove duplicates
                cleaned_row.append(cleaned)
        value["row_headers"] = cleaned_row

        # Clean column headers
        cleaned_col = []
        for header in value["column_headers"]:
            cleaned = header
            for old, new in replacements.items():
                cleaned = cleaned.replace(old, new)
            if cleaned not in cleaned_col:  # Remove duplicates
                cleaned_col.append(cleaned)
        value["column_headers"] = cleaned_col

    print(f"✅ Cleaned headers for {len(values)} values")

    return {"values_with_metadata": values}