# -----
# value_retriever.py
# -----
"""
value_retriever.py
==================
OCR each detected cell, clean the text, and emit a JSON‑serialisable
dict enriched with row/column IDs.
"""
from __future__ import annotations

import re
from typing import List, Dict, Any
import cv2
import numpy as np
import pytesseract
from PIL import Image

from grid_builder import Cell

NUM_RE = re.compile(r"-?\d[\d\. ,]*\d")


class ValueRetriever:
    def __init__(self, lang: str = "eng") -> None:
        # Use a Tesseract whitelist to speed up numeric OCR.
        self.tess_config = (
            "--oem 3 --psm 7 -c tessedit_char_whitelist=0123456789.,-"
        )
        self.lang = lang
        self._rx_number = re.compile(r"[0-9][0-9 .,:-]*")

    # ------------------------------------------------------------------ #
    #  Public API
    # ------------------------------------------------------------------ #

    def ocr_cells(
            self, cells: List[Cell], full_page: Image.Image
    ) -> List[Dict[str, Any]]:
        out: list[dict] = []
        for cell in cells:
            crop = full_page.crop(cell.bbox)
            text = pytesseract.image_to_string(
                crop, lang=self.lang, config=self.tess_config
            ).strip()

            number = self._extract_number(text)

            out.append(
                {
                    "page": cell.page,
                    "bbox": cell.bbox,
                    "row": cell.row,
                    "col": cell.col,
                    "raw_text": text,
                    "value": number,
                }
            )
        return out

    # ------------------------------------------------------------------ #
    #  Helpers
    # ------------------------------------------------------------------ #

    def _extract_number(self, txt: str) -> float | None:
        """
        Returns a float if numeric text is found, else None.
        Handles European decimal comma.
        """
        match = self._rx_number.search(txt)
        if match:
            cleaned = match.group(0)
            # Remove thousands separators in either style
            cleaned = cleaned.replace(" ", "").replace(".", "").replace(",", ".")
            try:
                return float(cleaned)
            except ValueError:
                return None
        return None

    def _preprocess_patch(patch: np.ndarray) -> np.ndarray:
        gray = cv2.cvtColor(patch, cv2.COLOR_BGR2GRAY)
        gray = cv2.GaussianBlur(gray, (3, 3), 0)
        _, bin_ = cv2.threshold(gray, 0, 255,
                                cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        return 255 - bin_  # white text on black BG → helps Tesseract

    def _to_number(txt: str) -> float | None:
        m = NUM_RE.search(txt)
        if not m:
            return None
        cleaned = m.group(0)
        cleaned = cleaned.replace(" ", "").replace(".", "").replace(",", ".")
        try:
            return float(cleaned)
        except ValueError:
            return None
