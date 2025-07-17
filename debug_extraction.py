# debug_extraction.py
import json
import os
from pdf_parser import extract_all_elements
from grid_builder import build_logical_grid
from value_retriever import retrieve_values_from_grid


def debug_extraction(pdf_path):
    """Debug the extraction process step by step"""

    print("=" * 60)
    print("DEBUG: PDF Table Extraction")
    print("=" * 60)

    # Step 1: Extract elements
    print("\n1. EXTRACTING ELEMENTS...")
    text_blocks, horiz_lines, vert_lines = extract_all_elements(pdf_path)

    print(f"\nFound {len(text_blocks)} text blocks:")
    # Show first 10 text blocks
    for i, block in enumerate(text_blocks[:10]):
        print(f"  {i}: '{block['content']}' at {block['bbox']}")
    if len(text_blocks) > 10:
        print(f"  ... and {len(text_blocks) - 10} more")

    # Step 2: Build grid
    print("\n2. BUILDING GRID...")
    grid = build_logical_grid(text_blocks, horiz_lines, vert_lines)

    print(f"\nGrid dimensions: {len(grid)} rows x {len(grid[0]) if grid else 0} columns")

    # Print grid with coordinates
    if grid:
        print("\nGrid content (showing non-empty cells):")
        for r, row in enumerate(grid):
            for c, cell in enumerate(row):
                if cell.strip():
                    print(f"  [{r},{c}]: '{cell}'")

    # Step 3: Extract values
    print("\n3. EXTRACTING VALUES...")
    json_output = retrieve_values_from_grid(grid)
    values = json.loads(json_output)

    print(f"\nExtracted {len(values)} values")

    # Show all values found
    print("\nAll numeric values found:")
    expected_values = [
        "23,00", "24,00", "26,00",  # Col1 for M1
        "25,40", "25,10", "25,20",  # Col3B for M1
        "115,50", "125,50", "105,50",  # Col2B for M1
        "50,00", "54,00",  # Col4A, Col4B for M1
        "35,00", "35,00",  # Middle values
        "21,00",  # Col1 for M2
        "135,40", "1589,10", "135,40", "1589,10",  # Col2A/2B for M2
        "80,00", "59,00",  # Col4A, Col4B for M2
        "15,00",  # Col1 for M4
        "57,00", "51,00", "57,00", "51,00",  # Col2A/2B for M4
        "62,00", "19,00", "62,00", "19,00",  # Col2A/2B for M5
        "16,00", "45,00"  # Col4A, Col4B for M4
    ]

    found_values = [v['value'] for v in values]
    print(f"\nFound values: {found_values}")
    print(f"\nExpected ~{len(expected_values)} values")

    missing = []
    for exp in expected_values:
        if exp not in found_values:
            missing.append(exp)

    if missing:
        print(f"\nMissing values: {missing}")

    # Save debug info
    debug_dir = "debug_output"
    os.makedirs(debug_dir, exist_ok=True)

    # Save text blocks
    with open(os.path.join(debug_dir, "text_blocks.json"), "w") as f:
        json.dump([{"content": b["content"], "bbox": b["bbox"]} for b in text_blocks], f, indent=2)

    # Save grid
    with open(os.path.join(debug_dir, "grid.json"), "w") as f:
        json.dump(grid, f, indent=2)

    # Save extracted values
    with open(os.path.join(debug_dir, "values.json"), "w") as f:
        f.write(json_output)

    print(f"\nDebug files saved to {debug_dir}/")
    print("  - text_blocks.json: All text found by OCR")
    print("  - grid.json: The constructed grid")
    print("  - values.json: Extracted values with context")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Debug PDF extraction")
    parser.add_argument("pdf_path", help="Path to PDF file")
    args = parser.parse_args()

    debug_extraction(args.pdf_path)