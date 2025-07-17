# grid_builder.py
from typing import List, Dict, Any, Tuple
import statistics


def build_logical_grid(
        text_blocks: List[Dict[str, Any]],
        horiz_lines: List[Tuple],
        vert_lines: List[Tuple]
) -> List[List[str]]:
    """
    Constructs a logical 2D grid from text blocks and detected lines.
    """
    print("--- GRID BUILDER: Constructing grid from text and line evidence ---")
    if not text_blocks:
        return []

    # Extract unique x and y coordinates from lines and text blocks
    x_coords = set()
    y_coords = set()

    # Add line coordinates
    for x1, y1, x2, y2 in vert_lines:
        x_coords.add(x1)
    for x1, y1, x2, y2 in horiz_lines:
        y_coords.add(y1)

    # Add text block boundaries
    for block in text_blocks:
        x0, y0, x1, y1 = block['bbox']
        x_coords.add(x0)
        x_coords.add(x1)
        y_coords.add(y0)
        y_coords.add(y1)

    # Sort coordinates
    x_coords = sorted(list(x_coords))
    y_coords = sorted(list(y_coords))

    # Cluster nearby coordinates
    cols = _cluster_coords(x_coords, tolerance=30)
    rows = _cluster_coords(y_coords, tolerance=20)

    if len(cols) < 2 or len(rows) < 2:
        return []

    # Create empty grid
    grid = [['' for _ in range(len(cols) - 1)] for _ in range(len(rows) - 1)]

    # Place text blocks in grid
    for block in text_blocks:
        x0, y0, x1, y1 = block['bbox']
        x_center = (x0 + x1) / 2
        y_center = (y0 + y1) / 2

        # Find cell indices
        r_idx = _find_index(y_center, rows)
        c_idx = _find_index(x_center, cols)

        if r_idx is not None and c_idx is not None:
            # Handle merged cells by checking text block span
            r_span = 1
            c_span = 1

            # Check if text spans multiple cells
            for i in range(r_idx + 1, len(rows) - 1):
                if rows[i] < y1 - 10:
                    r_span += 1
                else:
                    break

            for i in range(c_idx + 1, len(cols) - 1):
                if cols[i] < x1 - 10:
                    c_span += 1
                else:
                    break

            # Place text in primary cell
            if grid[r_idx][c_idx]:
                grid[r_idx][c_idx] += " " + block['content']
            else:
                grid[r_idx][c_idx] = block['content']

    print(f"--- GRID BUILDER: Created grid with {len(rows) - 1} rows and {len(cols) - 1} columns ---")
    return grid


def _cluster_coords(coords: List[float], tolerance: int) -> List[int]:
    """Clusters nearby coordinates into representative points."""
    if not coords:
        return []

    coords = sorted(coords)
    clusters = []
    current_cluster = [coords[0]]

    for coord in coords[1:]:
        if coord - current_cluster[-1] <= tolerance:
            current_cluster.append(coord)
        else:
            # Use minimum of cluster to preserve boundaries
            clusters.append(min(current_cluster))
            current_cluster = [coord]

    clusters.append(min(current_cluster))
    return sorted(list(set(clusters)))


def _find_index(coord: float, boundaries: List[int]) -> int:
    """Finds which cell a coordinate belongs to."""
    for i in range(len(boundaries) - 1):
        if boundaries[i] <= coord <= boundaries[i + 1]:
            return i
    # If not found, return closest
    if coord < boundaries[0]:
        return 0
    return len(boundaries) - 2