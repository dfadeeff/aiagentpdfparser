# agents/value_retriever.py
import json
from typing import List


def retrieve_values_from_grid(grid: List[List[str]]) -> str:
    """
    Parses the logical grid to extract structured data. This version uses a
    "grid propagation" method to correctly handle complex merged cells.
    """
    print("--- VALUE RETRIEVER (SMART): Analyzing grid with propagation logic. ---")
    if not grid:
        return "[]"

    rows = len(grid)
    cols = len(grid[0])

    # --- Step 1: Grid Propagation ---
    # Create a copy of the grid to fill in the blanks from merged cells.
    # This makes header lookups trivial and reliable.
    propagated_grid = [row[:] for row in grid]

    # Propagate downwards
    for c in range(cols):
        for r in range(1, rows):
            if not propagated_grid[r][c] and propagated_grid[r - 1][c]:
                propagated_grid[r][c] = propagated_grid[r - 1][c]

    # Propagate sideways
    for r in range(rows):
        for c in range(1, cols):
            if not propagated_grid[r][c] and propagated_grid[r][c - 1]:
                propagated_grid[r][c] = propagated_grid[r][c - 1]

    # --- Step 2: Extract Values and Context ---
    final_output = []

    def is_numeric(s):
        # A robust check for strings like "23,00" or "1.589,10"
        return s and any(char.isdigit() for char in s) and "," in s

    def is_clean_header(s, current_value):
        # A header should not be empty, not be the value itself, and not be another number.
        return s and s != current_value and not is_numeric(s)

    # Find all numeric cells in the ORIGINAL grid
    for r, row in enumerate(grid):
        for c, cell_content in enumerate(row):
            if is_numeric(cell_content):
                row_context = set()
                # Find Row Context using the propagated grid
                for i in range(c - 1, -1, -1):
                    header = propagated_grid[r][i]
                    if is_clean_header(header, cell_content):
                        row_context.add(header)

                col_context = set()
                # Find Column Context using the propagated grid
                for i in range(r - 1, -1, -1):
                    header = propagated_grid[i][c]
                    if is_clean_header(header, cell_content):
                        col_context.add(header)

                final_output.append({
                    "value": cell_content,
                    "row_context": sorted(list(row_context)),
                    "column_context": sorted(list(col_context))
                })

    print("--- VALUE RETRIEVER (SMART): Extraction complete. ---")
    return json.dumps(final_output, indent=2)