# simple_extractor.py
import fitz  # PyMuPDF
import pytesseract
from PIL import Image
import io
import cv2
import numpy as np
import json
import re
import os
import argparse


def extract_values_from_pdf(pdf_path: str):
    """
    Extracts all numeric table values from the PDF using a simple, direct OCR approach.
    This function contains the proven logic from the original direct_test.py.
    """
    print("=" * 60)
    print("SIMPLE & DIRECT PDF VALUE EXTRACTOR")
    print("=" * 60)

    try:
        doc = fitz.open(pdf_path)
        page = doc.load_page(0)

        # --- The Core Logic ---
        # 1. Render at a reasonable resolution. 2x is enough for this clean PDF.
        mat = fitz.Matrix(2, 2)
        pix = page.get_pixmap(matrix=mat)
        img_data = pix.tobytes("png")
        pil_img = Image.open(io.BytesIO(img_data))

        # 2. Convert to simple grayscale. NO other processing is needed.
        # This is the key to why this method works. It doesn't try to "fix" what isn't broken.
        gray_img = cv2.cvtColor(np.array(pil_img), cv2.COLOR_RGB2GRAY)

        # 3. Run OCR to get detailed data.
        print("Running OCR on the clean grayscale image...")
        ocr_data = pytesseract.image_to_data(gray_img, output_type=pytesseract.Output.DICT)

        # 4. Loop through results and find only valid, complete numbers.
        extracted_values = []
        for i in range(len(ocr_data['text'])):
            text = ocr_data['text'][i].strip()

            # Use a strict regex to find numbers in the "XX,XX" format.
            # This is the most reliable way to filter out noise.
            if re.match(r'^\d{1,4},\d{2}$', text):
                extracted_values.append({
                    "value": text,
                    "confidence": int(ocr_data['conf'][i]),
                    "bbox": {
                        "x0": ocr_data['left'][i] // 2,
                        "y0": ocr_data['top'][i] // 2,
                        "x1": (ocr_data['left'][i] + ocr_data['width'][i]) // 2,
                        "y1": (ocr_data['top'][i] + ocr_data['height'][i]) // 2
                    }
                })

        print(f"\nSUCCESS! Found exactly {len(extracted_values)} numeric values.")

        # Sort values by their position on the page (top-to-bottom, left-to-right)
        extracted_values.sort(key=lambda item: (item['bbox']['y0'], item['bbox']['x0']))

        # Print the final, clean list
        final_value_list = [item['value'] for item in extracted_values]
        print(final_value_list)

        # Save the clean results to a file
        output_dir = "output"
        os.makedirs(output_dir, exist_ok=True)
        output_path = os.path.join(output_dir, "simple_extraction.json")

        with open(output_path, "w") as f:
            json.dump({
                "source_pdf": pdf_path,
                "extracted_count": len(extracted_values),
                "values": extracted_values
            }, f, indent=2)

        print(f"\nResults saved to: {output_path}")
        print("=" * 60)

        return extracted_values

    except Exception as e:
        print(f"\nAn error occurred: {e}")
        return []


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="A simple, direct PDF table value extractor.")
    parser.add_argument("pdf_path", help="Path to the PDF file to process.")
    args = parser.parse_args()

    if not os.path.exists(args.pdf_path):
        print(f"ERROR: File not found at '{args.pdf_path}'")
    else:
        extract_values_from_pdf(args.pdf_path)