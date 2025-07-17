# main.py
import argparse
import os
import json
from agents.pdf_parser import extract_raw_text_blocks
from agents.grid_builder import build_logical_grid
from agents.value_retriever import retrieve_values_from_grid

def main():
    """
    Main function to orchestrate the deterministic table extraction pipeline.
    """
    parser = argparse.ArgumentParser(
        description="A deterministic pipeline to extract data from a complex PDF table."
    )
    parser.add_argument("pdf_path", help="Path to the PDF file.")
    args = parser.parse_args()

    if not os.path.exists(args.pdf_path):
        print(f"FATAL: File not found at '{args.pdf_path}'")
        return

    # --- THE ASSEMBLY LINE ---
    # Station 1: Get raw materials with coordinates
    raw_blocks = extract_raw_text_blocks(args.pdf_path)
    if not raw_blocks:
        print("FAILURE: Could not extract any text from the PDF.")
        return

    # Station 2: Build the logical grid architecture
    logical_grid = build_logical_grid(raw_blocks)
    if not logical_grid:
        print("FAILURE: Could not build a logical grid from the PDF content.")
        return

    # Station 3: Assemble the final values from the grid
    final_json_output = retrieve_values_from_grid(logical_grid)

    # --- SAVE THE FINAL PRODUCT ---
    output_dir = "output"
    os.makedirs(output_dir, exist_ok=True)
    output_path = os.path.join(output_dir, "extracted_data_deterministic.json")

    with open(output_path, "w") as f:
        f.write(final_json_output)

    print("\n" + "="*50)
    print("--- SUCCESS ---")
    print(f"All values extracted and saved to: {output_path}")
    print("="*50)


if __name__ == "__main__":
    main()