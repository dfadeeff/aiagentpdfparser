"""
grid_builder.py
===============
Finds table regions on a page and splits them into a grid of cells
based on detected horizontal and vertical lines. Uses classical
computer‑vision morphology so you do not need GPU inference.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import List, Tuple, Dict, Any

import cv2
import numpy as np
from PIL import Image


@dataclass
class Cell:
    page: int
    bbox: Tuple[int, int, int, int]  # (x0, y0, x1, y1)
    row: int
    col: int


class GridBuilder:
    def __init__(
            self,
            min_line_length: int = 50,
            line_thickness: int = 2,
            line_gap: int = 3,
    ) -> None:
        self.min_line_length = min_line_length
        self.line_thickness = line_thickness
        self.line_gap = line_gap

    # --------------------------------------------------------------------- #
    #  Public API
    # --------------------------------------------------------------------- #

    def extract_tables(
            self, pil_img: Image.Image, page: int
    ) -> List[Dict[str, Any]]:
        """
        Return a list of dicts:
        {
            "page": page,
            "bbox": (x0,y0,x1,y1),
            "image": table_roi_pil
        }
        """
        cv_img = cv2.cvtColor(np.array(pil_img), cv2.COLOR_RGB2GRAY)
        # Adaptive threshold gives better results on scans.
        bin_img = cv2.adaptiveThreshold(
            cv_img, 255, cv2.ADAPTIVE_THRESH_MEAN_C, cv2.THRESH_BINARY_INV, 15, 10
        )

        # Find contours: assume the largest rectangles are tables.
        contours, _ = cv2.findContours(
            bin_img, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE
        )
        tables: list[dict] = []
        for cnt in contours:
            x, y, w, h = cv2.boundingRect(cnt)
            # Heuristic: ignore tiny blocks
            if w < 200 or h < 100:
                continue
            roi = pil_img.crop((x, y, x + w, y + h))
            tables.append({"page": page, "bbox": (x, y, x + w, y + h), "image": roi})
        # Sort top‑to‑bottom, left‑to‑right for deterministic order.
        tables.sort(key=lambda d: (d["bbox"][1], d["bbox"][0]))
        return tables

    def extract_cells(self, table_record: Dict[str, Any]) -> List[Cell]:
        pil_img: Image.Image = table_record["image"]
        page: int = table_record["page"]
        x_offset, y_offset, _, _ = table_record["bbox"]

        gray = cv2.cvtColor(np.array(pil_img), cv2.COLOR_RGB2GRAY)
        thresh = cv2.adaptiveThreshold(
            gray, 255, cv2.ADAPTIVE_THRESH_MEAN_C, cv2.THRESH_BINARY_INV, 15, 10
        )

        # --- Detect horizontal lines ------------------------------------- #
        horiz_kernel = cv2.getStructuringElement(
            cv2.MORPH_RECT, (25, 1)
        )  # long horizontal
        detect_horiz = cv2.morphologyEx(thresh, cv2.MORPH_OPEN, horiz_kernel, iterations=2)

        # --- Detect vertical lines --------------------------------------- #
        vert_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (1, 25))
        detect_vert = cv2.morphologyEx(thresh, cv2.MORPH_OPEN, vert_kernel, iterations=2)

        # --- Combine to get grid lines ----------------------------------- #
        grid = cv2.addWeighted(detect_horiz, 0.5, detect_vert, 0.5, 0.0)
        grid = cv2.dilate(grid, None, iterations=1)

        # Find intersections to estimate rows/cols
        intersections = cv2.bitwise_and(detect_horiz, detect_vert)
        ys, xs = np.where(intersections > 0)
        unique_x = self._cluster_1d(xs)
        unique_y = self._cluster_1d(ys)

        # Guard against degenerate detection
        if len(unique_x) < 2 or len(unique_y) < 2:
            return []

        unique_x.sort()
        unique_y.sort()

        cells: list[Cell] = []
        for r in range(len(unique_y) - 1):
            for c in range(len(unique_x) - 1):
                x0, y0 = unique_x[c], unique_y[r]
                x1, y1 = unique_x[c + 1], unique_y[r + 1]
                # Discard whitespace cells
                cell_roi = thresh[y0:y1, x0:x1]
                if cv2.countNonZero(cell_roi) < 50:
                    continue
                cells.append(
                    Cell(
                        page=page,
                        bbox=(x0 + x_offset, y0 + y_offset, x1 + x_offset, y1 + y_offset),
                        row=r,
                        col=c,
                    )
                )

        return cells

    # ------------------------------------------------------------------ #
    #  Helpers
    # ------------------------------------------------------------------ #

    def _cluster_1d(self, points: np.ndarray, eps: int | None = None) -> List[int]:
        """
        Simple 1‑D DBSCAN‑like clustering: collapses points that are within
        `eps` pixels of each other into a single representative (the median).
        """
        if eps is None:
            eps = self.line_gap
        if len(points) == 0:
            return []

        sorted_pts = np.sort(points)
        clusters: list[list[int]] = [[int(sorted_pts[0])]]
        for p in sorted_pts[1:]:
            if abs(p - clusters[-1][-1]) <= eps:
                clusters[-1].append(int(p))
            else:
                clusters.append([int(p)])
        # Use median of each cluster as representative line.
        return [int(np.median(c)) for c in clusters]

    def _tighten_boxes(boxes: List[Cell], img: np.ndarray) -> List[Cell]:
        """Shrink each bbox to the minimal contour that still contains ink.
        Prevents blank-patch OCR."""
        shrunk = []
        for c in boxes:
            x0, y0, x1, y1 = c.bbox
            patch = img[y0:y1, x0:x1]
            gray = cv2.cvtColor(patch, cv2.COLOR_BGR2GRAY)
            _, thresh = cv2.threshold(gray, 200, 255, cv2.THRESH_BINARY_INV)
            ys, xs = np.where(thresh > 0)
            if ys.size == 0:  # blank cell → keep original
                shrunk.append(c)
                continue
            ny0, ny1 = ys.min(), ys.max()
            nx0, nx1 = xs.min(), xs.max()
            # pad 2 px to avoid cropping the stroke
            shrunk.append(Cell(c.page, (x0 + nx0 - 2, y0 + ny0 - 2, x0 + nx1 + 2, y0 + ny1 + 2),
                               c.row, c.col))
        return shrunk

    def _deduce_colspans(grid: List[List[Cell]]) -> List[List[Cell]]:
        """
        If two horizontally-adjacent cells have almost identical x0/x1,
        collapse them (PDF has merged header). Keeps leftmost bbox.
        """
        merged = []
        for row in grid:
            new_row = []
            skip_next = False
            for i, cell in enumerate(row):
                if skip_next:
                    skip_next = False
                    continue
                if (i < len(row) - 1 and
                        abs(row[i].bbox[0] - row[i + 1].bbox[0]) < 3 and
                        abs(row[i].bbox[2] - row[i + 1].bbox[2]) < 3):
                    # treat as one big cell
                    skip_next = True
                new_row.append(cell)
            merged.append(new_row)
        return merged
