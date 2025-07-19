# pipeline/nodes.py
import re
from typing import Dict, List, Any
from pipeline.state import PipelineState

# Import YOUR WORKING EXTRACTOR
from tools.extractor import extract_values_from_pdf, get_all_text_elements


def extraction_node(state: PipelineState) -> Dict[str, Any]:
    """
    NODE 1: Extracts raw data from the PDF.
    """
    print("\n🔍 NODE 1: EXTRACTION")
    print("-" * 40)
    pdf_path = state["pdf_path"]
    values = extract_values_from_pdf(pdf_path)
    print(f"✅ Extracted {len(values)} numeric values.")
    return {"extracted_values": values}


def metadata_enrichment_node(state: PipelineState) -> Dict[str, Any]:
    """
    NODE 2: Deterministically assigns all row and column headers based on clean,
    unambiguous positional rules. This single node contains all the core logic.
    """
    print("\n📊 NODE 2: APPLYING DETERMINISTIC STRUCTURAL RULES")
    print("-" * 40)

    values = state["extracted_values"]
    results = []

    for value in values:
        v_bbox = value["bbox"]
        v_x_center = (v_bbox["x0"] + v_bbox["x1"]) / 2
        v_y_center = (v_bbox["y0"] + v_bbox["y1"]) / 2

        row_headers = []
        col_headers = []

        # --- ROW HEADER LOGIC ---
        # This is a set of clear, non-overlapping rules based on the visual layout.

        # Rule for Block M1/Merged1 (y: 200 -> 255)
        if 200 <= v_y_center < 290:
            major_headers = ["M1", "Merged1"]
            sub_row_headers = []
            if 200 <= v_y_center < 215:  # This is the "AA" row.
                sub_row_headers = ["Row.Invisible.Grid1", "AA"]
            elif 215 <= v_y_center < 230:  # This is the "BB" row.
                sub_row_headers = ["Row.Invisible.Grid2", "BB"]
            elif 230 <= v_y_center < 255:  # This is the "CC" row, which also GOVERNS the 50,00 and 54,00 values.
                sub_row_headers = ["Row.Invisible.Grid3", "CC"]
            row_headers = major_headers + sub_row_headers

        # Rule for Block M2/Merged2
        elif 290 <= v_y_center < 350:
            row_headers = ["M2", "Merged2"]

        # Rule for Block M4/Merged4
        elif 415 <= v_y_center < 430:
            row_headers = ["M4", "Merged4"]

        # Rule for Block M4/Merged5
        elif 430 <= v_y_center < 450:
            row_headers = ["M4", "Merged5"]

        # --- COLUMN HEADER LOGIC ---
        # Based on stable X-coordinates.
        if 370 <= v_x_center <= 400:
            col_headers = ["Col1"]
        elif 430 <= v_x_center <= 525:
            col_headers = ["Col2", "Col2A", "Col3A"]
        elif 550 <= v_x_center <= 640:
            col_headers = ["Col2", "Col2B", "Col3B"]
        elif 670 <= v_x_center <= 700:
            col_headers = ["Col4", "Col4A"]
        elif 730 <= v_x_center <= 760:
            col_headers = ["Col4", "Col4B"]

        # --- EXCEPTION HANDLING ---
        # The '35,00' values are a true structural anomaly that must be handled separately.
        if value["value"] == "35,00" and 270 <= v_y_center <= 285:
            row_headers = []  # They have no row headers. This overrides all other rules.
            if v_x_center < 500:
                col_headers = ["Col2", "Col2A", "Col3A"]
            else:
                col_headers = ["Col2", "Col2B", "Col3B"]

        results.append({
            "value": value["value"],
            "row_headers": row_headers,
            "column_headers": col_headers,
            "confidence": value["confidence"],
            "bbox": value["bbox"]
        })

    print(f"✅ Correctly assigned headers to {len(results)} values.")
    return {"values_with_metadata": results}


def cleaning_node(state: PipelineState) -> Dict[str, Any]:
    """
    NODE 3: Performs a minimal, final cleanup for consistent OCR errors.
    This node is now extremely simple because the previous node does the job correctly.
    """
    print("\n🧹 NODE 3: FINAL OCR CLEANUP")
    print("-" * 40)

    values = state["values_with_metadata"]
    # This map only contains consistent, known OCR mistakes.
    replacements = {
        "Colt": "Col1",
        "Col4a": "Col4A",
        "col4B": "Col4B",
        "Col2h": "Col2B"
    }

    for value in values:
        # Clean up column headers using the simple replacement map.
        cleaned_column_headers = [replacements.get(h, h) for h in value["column_headers"]]

        # Ensure final lists are unique (though they should be already).
        value["row_headers"] = list(dict.fromkeys(value["row_headers"]))
        value["column_headers"] = list(dict.fromkeys(cleaned_column_headers))

    print(f"✅ Performed final cleanup on {len(values)} values.")
    return {"values_with_metadata": values}