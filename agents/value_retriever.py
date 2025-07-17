# value_retriever.py
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

    # Create propagated grid for merged cells
    propagated_grid = [row[:] for row in grid]

    # Propagate values downward for merged cells
    for r in range(1, rows):
        for c in range(cols):
            if not propagated_grid[r][c].strip() and propagated_grid[r - 1][c].strip():
                # Check if this is likely a merged cell (not just empty)
                if r < rows - 1 and not grid[r + 1][c].strip():
                    propagated_grid[r][c] = propagated_grid[r - 1][c]

    # Propagate values rightward for merged cells
    for r in range(rows):
        for c in range(1, cols):
            if not propagated_grid[r][c].strip() and propagated_grid[r][c - 1].strip():
                # Check if this is likely a merged cell
                if c < cols - 1 and not grid[r][c + 1].strip():
                    propagated_grid[r][c] = propagated_grid[r][c - 1]

    # Extract all values with their context
    results = []

    # Helper functions
    def is_numeric(s: str) -> bool:
        token = s.strip()
        # 1) must look like European decimal with exactly two digits
        if not re.fullmatch(r"\d{1,5},\d{2}", token):
            return False
        # 2) now double-check by float-cast on a cleaned version
        normalized = token.replace(".", "").replace(",", ".")
        try:
            float(normalized)
            return True
        except ValueError:
            return False

    def clean_value(s: str) -> str:
        """Clean and standardize numeric values"""
        if not s:
            return ""
        # Remove minus sign prefix and handle European format
        s = s.strip()
        if s.startswith("-"):
            s = s[1:]
        return s

    def get_row_headers(r: int, c: int) -> List[str]:
        """Get all row headers for a cell"""
        headers = []
        # Scan left from the cell
        for i in range(c - 1, -1, -1):
            content = propagated_grid[r][i].strip()
            if content and not is_numeric(content):
                headers.append(content)
        return headers[::-1]  # Reverse to get left-to-right order

    def get_column_headers(r: int, c: int) -> List[str]:
        """Get all column headers for a cell"""
        headers = []
        # Scan up from the cell
        for i in range(r - 1, -1, -1):
            content = propagated_grid[i][c].strip()
            if content and not is_numeric(content):
                headers.append(content)
        return headers[::-1]  # Reverse to get top-to-bottom order

    # Find all numeric values in the original grid
    for r in range(rows):
        for c in range(cols):
            cell_content = grid[r][c].strip()
            if cell_content and is_numeric(cell_content):
                # Get context from propagated grid
                row_headers = get_row_headers(r, c)
                col_headers = get_column_headers(r, c)

                # Add table title if in top-left area
                table_title = None
                if r > 0 and c > 0:
                    # Check top-left corner for table title
                    for i in range(min(3, rows)):
                        for j in range(min(3, cols)):
                            content = propagated_grid[i][j].strip()
                            if content and "Table" in content:
                                table_title = content
                                break
                        if table_title:
                            break

                result = {
                    "value": clean_value(cell_content),
                    "row": r,
                    "col": c,
                    "row_headers": row_headers,
                    "column_headers": col_headers
                }

                if table_title and table_title not in col_headers:
                    result["table_title"] = table_title

                results.append(result)

    print(f"--- VALUE RETRIEVER: Extracted {len(results)} values with context ---")
    return json.dumps(results, indent=2, ensure_ascii=False)
