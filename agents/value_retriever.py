# agents/value_retriever.py
import json
import re
from typing import List, Dict, Any, Set


def retrieve_values_from_grid(grid: List[List[str]]) -> str:
    """
    Parses the logical grid to extract structured data with proper context.
    """
    print("--- VALUE RETRIEVER: Analyzing grid with hierarchical context ---")
    if not grid or len(grid) == 0:
        return "[]"

    rows = len(grid)
    cols = len(grid[0]) if rows > 0 else 0

    if rows == 0 or cols == 0:
        return "[]"

    # Define helper functions FIRST before using them
    def is_numeric(s: str) -> bool:
        """Check if string contains a numeric value"""
        if not s or not isinstance(s, str):
            return False

        token = s.strip()

        # Handle negative numbers
        if token.startswith("-"):
            token = token[1:]

        # Check for European format (e.g., "23,00", "135,40", "1589,10")
        if re.match(r'^\d{1,4},\d{2}$', token):
            return True

        # Check for plain integers (e.g., "21", "50")
        if re.match(r'^\d+$', token):
            return True

        # Check for decimal with period
        if re.match(r'^\d+\.\d+$', token):
            return True

        return False

    def clean_value(s: str) -> str:
        """Clean and standardize numeric values"""
        if not s:
            return ""
        # Keep original format but strip whitespace
        return s.strip()

    def get_row_headers(r: int, c: int, prop_grid) -> List[str]:
        """Get all row headers for a cell"""
        headers = []
        seen = set()

        # Scan left from the cell
        for i in range(c - 1, -1, -1):
            content = prop_grid[r][i].strip()
            if content and not is_numeric(content) and content not in seen:
                # Filter out noise
                if len(content) > 1 and content not in ['|', '-', '=', '[', ']', '(', ')']:
                    headers.append(content)
                    seen.add(content)

        return headers[::-1]  # Reverse to get left-to-right order

    def get_column_headers(r: int, c: int, prop_grid) -> List[str]:
        """Get all column headers for a cell"""
        headers = []
        seen = set()

        # Scan up from the cell
        for i in range(r - 1, -1, -1):
            content = prop_grid[i][c].strip()
            if content and not is_numeric(content) and content not in seen:
                # Filter out noise
                if len(content) > 1 and content not in ['|', '-', '=', '[', ']', '(', ')']:
                    headers.append(content)
                    seen.add(content)

        return headers[::-1]  # Reverse to get top-to-bottom order

    # Create propagated grid for merged cells
    propagated_grid = [row[:] for row in grid]

    # More aggressive propagation - fill empty cells from neighbors
    # First pass: propagate downward
    for r in range(1, rows):
        for c in range(cols):
            if not propagated_grid[r][c].strip() and propagated_grid[r - 1][c].strip():
                # Propagate non-numeric content downward
                if not is_numeric(propagated_grid[r - 1][c]):
                    propagated_grid[r][c] = propagated_grid[r - 1][c]

    # Second pass: propagate rightward
    for r in range(rows):
        for c in range(1, cols):
            if not propagated_grid[r][c].strip() and propagated_grid[r][c - 1].strip():
                # Propagate non-numeric content rightward
                if not is_numeric(propagated_grid[r][c - 1]):
                    propagated_grid[r][c] = propagated_grid[r][c - 1]

    # Extract all values with their context
    results = []

    # Find all numeric values in the original grid
    total_numeric_found = 0

    for r in range(rows):
        for c in range(cols):
            cell_content = grid[r][c].strip()

            if not cell_content:
                continue

            # Split cell content by spaces to handle multiple values in one cell
            parts = cell_content.split()

            for part in parts:
                part = part.strip()
                if part and is_numeric(part):
                    total_numeric_found += 1

                    # Get context from propagated grid
                    row_headers = get_row_headers(r, c, propagated_grid)
                    col_headers = get_column_headers(r, c, propagated_grid)

                    # Find table title if exists
                    table_title = None
                    for i in range(min(3, rows)):
                        for j in range(min(3, cols)):
                            content = propagated_grid[i][j].strip()
                            if content and "Table" in content:
                                table_title = content
                                break
                        if table_title:
                            break

                    result = {
                        "value": clean_value(part),
                        "row": r,
                        "col": c,
                        "row_headers": row_headers,
                        "column_headers": col_headers
                    }

                    if table_title:
                        result["table_title"] = table_title

                    results.append(result)

    print(f"--- VALUE RETRIEVER: Found {total_numeric_found} numeric values in grid ---")
    print(f"--- VALUE RETRIEVER: Extracted {len(results)} values with context ---")

    return json.dumps(results, indent=2, ensure_ascii=False)