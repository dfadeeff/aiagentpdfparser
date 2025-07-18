# main.py
import argparse
import os
import json
from pdf_parser import extract_all_elements
from grid_builder import build_logical_grid
from agents.value_retriever import retrieve_values_from_grid  # Fixed import


def print_grid_debug(grid):
    """Print grid for debugging"""
    print("\n--- DEBUG: Grid Structure ---")
    for i, row in enumerate(grid):
        print(f"Row {i}: {row}")
    print("--- End Grid Debug ---\n")


def main():
    """
    Main function to orchestrate the table extraction pipeline.
    """
    parser = argparse.ArgumentParser(
        description="Extract structured data from PDF tables"
    )
    parser.add_argument("pdf_path", help="Path to the PDF file")
    parser.add_argument("--debug", action="store_true", help="Enable debug output")
    args = parser.parse_args()

    if not os.path.exists(args.pdf_path):
        print(f"ERROR: File not found at '{args.pdf_path}'")
        return

    print("=" * 50)
    print("PDF TABLE EXTRACTION PIPELINE")
    print("=" * 50)

    # Step 1: Extract text and lines from PDF
    text_blocks, horiz_lines, vert_lines = extract_all_elements(args.pdf_path)
    if not text_blocks:
        print("ERROR: Could not extract any text from the PDF")
        return

    # Step 2: Build logical grid from extracted elements
    logical_grid = build_logical_grid(text_blocks, horiz_lines, vert_lines)
    if not logical_grid:
        print("ERROR: Could not build a logical grid from the PDF content")
        return

    if args.debug:
        print_grid_debug(logical_grid)

    # Step 3: Extract values with context
    final_json_output = retrieve_values_from_grid(logical_grid)

    # Save output
    output_dir = "output"
    os.makedirs(output_dir, exist_ok=True)

    # Save the extracted data
    output_path = os.path.join(output_dir, "extracted_data.json")
    with open(output_path, "w", encoding='utf-8') as f:
        f.write(final_json_output)

    # Also save the grid structure for reference
    grid_path = os.path.join(output_dir, "grid_structure.json")
    with open(grid_path, "w", encoding='utf-8') as f:
        json.dump(logical_grid, f, indent=2, ensure_ascii=False)

    print("\n" + "=" * 50)
    print("SUCCESS!")
    print(f"Extracted data saved to: {output_path}")
    print(f"Grid structure saved to: {grid_path}")
    print("=" * 50)

    # Print summary
    data = json.loads(final_json_output)
    print(f"\nSummary: Extracted {len(data)} values from the table")

    if data and args.debug:
        print("\nSample extracted values:")
        for item in data[:3]:
            print(f"- Value: {item['value']}")
            print(f"  Row headers: {item['row_headers']}")
            print(f"  Column headers: {item['column_headers']}")
            print()


if __name__ == "__main__":
    main()