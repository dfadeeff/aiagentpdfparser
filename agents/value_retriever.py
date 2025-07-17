# agents/value_retriever.py
import json
from typing import List, Dict, Any


def retrieve_values_from_grid(grid: List[List[str]]) -> str:
    """
    Parses the logical grid to extract structured data. This agent understands
    the table's specific layout rules and associations.
    """
    print("--- VALUE RETRIEVER: Extracting structured data from grid. ---")
    if not grid:
        return "[]"

    final_output = []

    # A simple helper to check if a string is a number in the format "123,45"
    def is_numeric(s):
        return s and "," in s and s.replace(",", "").replace(".", "").isdigit()

    # Iterate through every cell to find our data points (the numbers)
    for r, row in enumerate(grid):
        for c, cell_content in enumerate(row):
            if is_numeric(cell_content):
                row_context = []
                col_context = []

                # Find Row Context: Traverse left from the cell
                for i in range(c - 1, -1, -1):
                    # Check current row
                    if grid[r][i]: row_context.append(grid[r][i])
                    # Check rows above for vertically merged headers (like "Merged1")
                    # This is a simple heuristic that checks if the cell above is empty
                    for r_up in range(r - 1, -1, -1):
                        if grid[r_up][i] and not grid[r_up + 1][i]:
                            if grid[r_up][i] not in row_context:
                                row_context.append(grid[r_up][i])

                # Find Column Context: Traverse up from the cell
                for i in range(r - 1, -1, -1):
                    if grid[i][c]: col_context.append(grid[i][c])
                    # Check columns left for horizontally merged headers (like "Col2")
                    for c_left in range(c - 1, -1, -1):
                        if grid[i][c_left] and not grid[i][c_left + 1]:
                            if grid[i][c_left] not in col_context:
                                col_context.append(grid[i][c_left])

                final_output.append({
                    "value": cell_content,
                    # Reverse to get natural reading order
                    "row_context": list(reversed(row_context)),
                    "column_context": list(reversed(col_context))
                })

    print("--- VALUE RETRIEVER: Extraction complete. ---")
    return json.dumps(final_output, indent=2)