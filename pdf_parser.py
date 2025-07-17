"""
pdf_parser.py
=============
Utility for loading PDF pages and converting them to PIL images at a
stable DPI. Works for both born‑digital and scanned PDFs.
"""
from pathlib import Path
from typing import List

try:
    # PyMuPDF is slimmer than pdf2image because it does not require poppler.
    import fitz  # type: ignore
except ImportError:  # pragma: no cover
    raise ImportError("Install PyMuPDF: pip install pymupdf")

from PIL import Image


class PDFParser:
    def __init__(self, pdf_path: str | Path, dpi: int = 300) -> None:
        self.pdf_path = Path(pdf_path)
        if not self.pdf_path.exists():
            raise FileNotFoundError(self.pdf_path)
        self.dpi = dpi

    def to_images(self) -> List[Image.Image]:
        """Render each page of the PDF to a Pillow image."""
        doc = fitz.open(self.pdf_path)
        mat = fitz.Matrix(self.dpi / 72, self.dpi / 72)  # 72 pt per inch
        images: list[Image.Image] = []
        for page in doc:
            pix = page.get_pixmap(matrix=mat, alpha=False)
            img = Image.frombytes("RGB", (pix.width, pix.height), pix.samples)
            images.append(img)
        return images
