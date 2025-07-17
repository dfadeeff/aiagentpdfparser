# agents/grid_builder.py
from typing import List, Dict, Any

def build_logical_grid(text_blocks: List[Dict[str, Any]]) -> List[List[str]]:
    """
    Takes raw text blocks with coordinates and constructs a logical 2D grid.
    This is a purely deterministic process based on alignment.
    """
    print("--- GRID BUILDER: Constructing deterministic grid from coordinates. ---")
    if not text_blocks:
        return []

    # 1. Define vertical and horizontal grid lines from all bbox coordinates
    TOLERANCE = 1.0
    y_coords = sorted(list(set(block['bbox'][1] for block in text_blocks)))
    x_coords = sorted(list(set(block['bbox'][0] for block in text_blocks)))

    # Filter coordinates to create clear row/column boundaries
    rows = [y_coords[0]] if y_coords else []
    for y in y_coords[1:]:
        if y - rows[-1] > TOLERANCE:
            rows.append(y)

    cols = [x_coords[0]] if x_coords else []
    for x in x_coords[1:]:
        if x - cols[-1] > TOLERANCE:
            cols.append(x)

    # 2. Create an empty grid
    grid = [['' for _ in range(len(cols))] for _ in range(len(rows))]

    # 3. Place each text block into the grid
    for block in text_blocks:
        y0, x0 = block['bbox'][1], block['bbox'][0]
        # Find the closest row and column index
        row_idx = min(range(len(rows)), key=lambda i: abs(rows[i] - y0))
        col_idx = min(range(len(cols)), key=lambda i: abs(cols[i] - x0))
        grid[row_idx][col_idx] = block['content']

    print("--- GRID BUILDER: Grid construction complete. ---")
    return grid