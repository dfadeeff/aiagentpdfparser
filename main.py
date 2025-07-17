"""
main.py
=======
Command‑line entry point: run

    python main.py Table-Example-R.pdf -o extracted.json

and you will get a JSON array containing one record per cell with
(page, bbox, row, col, raw_text, value).
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import List, Dict, Any

from pdf_parser import PDFParser
from grid_builder import GridBuilder
from agents.value_retriever import ValueRetriever


def extract(pdf_path: str | Path) -> List[Dict[str, Any]]:
    parser = PDFParser(pdf_path)
    pages = parser.to_images()

    grid_builder = GridBuilder()
    ocr = ValueRetriever()

    all_cells: list[dict] = []
    for page_index, page_img in enumerate(pages, start=1):
        tables = grid_builder.extract_tables(page_img, page_index)
        for table in tables:
            cells = grid_builder.extract_cells(table)
            page_cells = ocr.ocr_cells(cells, page_img)
            all_cells.extend(page_cells)
    return all_cells


def cli() -> None:
    ap = argparse.ArgumentParser(description="Extract numeric cells from a PDF table")
    ap.add_argument("pdf", help="Path to PDF")
    ap.add_argument(
        "-o", "--out", default="extracted.json", help="Where to write the JSON output"
    )
    args = ap.parse_args()

    records = extract(args.pdf)
    with open(args.out, "w", encoding="utf-8") as fp:
        json.dump(records, fp, ensure_ascii=False, indent=2)
    print(f"Wrote {args.out} with {len(records)} cell records")


if __name__ == "__main__":
    cli()
