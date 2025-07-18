# tests/direct_test.py

"""
Direct test to see what's actually in the PDF.
This version is robust and will create its own output directory.
"""
import fitz
import pytesseract
from PIL import Image
import io
import cv2
import numpy as np
import json
import os  # <-- IMPORT THE OS MODULE
import sys
import re


def direct_pdf_test(pdf_path):
    """Directly test PDF extraction methods"""

    print("=" * 60)
    print("DIRECT PDF TEST (Corrected)")
    print("=" * 60)

    doc = fitz.open(pdf_path)
    page = doc.load_page(0)

    # Method 2: Render and OCR
    print("\n2. Testing OCR on rendered image...")
    mat = fitz.Matrix(2, 2)
    pix = page.get_pixmap(matrix=mat)
    img_data = pix.tobytes("png")

    # --- THE FIX IS HERE ---
    # Create the debug_output directory if it doesn't exist.
    output_dir = "debug_output"
    os.makedirs(output_dir, exist_ok=True)
    # --- END OF FIX ---

    # Save image for inspection
    output_image_path = os.path.join(output_dir, "page_render.png")
    with open(output_image_path, "wb") as f:
        f.write(img_data)
    print(f"Saved page render to {output_image_path}")

    # OCR the image
    pil_img = Image.open(io.BytesIO(img_data))
    gray = cv2.cvtColor(np.array(pil_img), cv2.COLOR_RGB2GRAY)
    ocr_data = pytesseract.image_to_data(gray, output_type=pytesseract.Output.DICT)

    # Find numeric values
    numeric_values = []
    for i in range(len(ocr_data['text'])):
        text = ocr_data['text'][i].strip()
        # Use a regex for precision
        if re.match(r'^\d{1,4},\d{2}$', text):
            numeric_values.append(text)

    # Sort for consistent order, just like in simple_extractor
    all_text_elements = []
    for i in range(len(ocr_data['text'])):
        if ocr_data['text'][i].strip():
            all_text_elements.append({
                'text': ocr_data['text'][i],
                'y': ocr_data['top'][i],
                'x': ocr_data['left'][i]
            })
    all_text_elements.sort(key=lambda e: (e['y'], e['x']))

    # Now extract the numeric values in the sorted order
    sorted_numeric_values = []
    for elem in all_text_elements:
        text = elem['text'].strip()
        if re.match(r'^\d{1,4},\d{2}$', text):
            sorted_numeric_values.append(text)

    print(f"\nFound {len(sorted_numeric_values)} numeric values:")
    print(sorted_numeric_values)

    # Save detailed output
    output_json_path = os.path.join(output_dir, "direct_test_results.json")
    with open(output_json_path, "w") as f:
        json.dump({
            'numeric_values': sorted_numeric_values
        }, f, indent=2)

    print(f"\nDetailed results saved to {output_json_path}")
    doc.close()


if __name__ == "__main__":
    if len(sys.argv) > 1:
        direct_pdf_test(sys.argv[1])
    else:
        # For simplicity, you can hardcode the path for testing
        direct_pdf_test("data/Table-Example-R.pdf")