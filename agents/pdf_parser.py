# agents/pdf_parser.py

import fitz  # PyMuPDF
import pytesseract
from PIL import Image
import io
from typing import List, Dict, Any


def extract_raw_text_blocks(pdf_path: str) -> List[Dict[str, Any]]:
    """
    Opens a PDF, converts it to an image, and uses Tesseract OCR to extract
    text blocks with their content and coordinates. This handles image-based PDFs.
    """
    print(f"--- PARSER (OCR ENABLED): Reading text from image-based PDF: {pdf_path} ---")
    text_elements = []
    try:
        # 1. Use PyMuPDF to render the PDF page as a high-quality image
        doc = fitz.open(pdf_path)
        page = doc.load_page(0)
        # Render at 300 DPI for high-quality OCR
        pix = page.get_pixmap(dpi=300)
        doc.close()

        # 2. Convert the image for Pytesseract
        img_bytes = pix.tobytes("png")
        image = Image.open(io.BytesIO(img_bytes))

        # 3. Use Pytesseract to perform OCR and get detailed data including coordinates
        # image_to_data returns a dictionary with keys: 'left', 'top', 'width', 'height', 'conf', 'text'
        ocr_data = pytesseract.image_to_data(image, output_type=pytesseract.Output.DICT)

        # 4. Process the raw OCR data into the standard format our grid builder expects
        num_items = len(ocr_data['text'])
        for i in range(num_items):
            # Tesseract gives confidence scores; we filter out low-confidence garbage
            confidence = int(ocr_data['conf'][i])
            text = ocr_data['text'][i].strip()

            if confidence > 40 and text:  # Only accept words Tesseract is reasonably sure about
                # Tesseract gives (left, top, width, height). We need (x0, y0, x1, y1).
                x0 = ocr_data['left'][i]
                y0 = ocr_data['top'][i]
                x1 = x0 + ocr_data['width'][i]
                y1 = y0 + ocr_data['height'][i]

                text_elements.append({
                    "content": text,
                    "bbox": (x0, y0, x1, y1)
                })

        if not text_elements:
            print(
                "--- PARSER (OCR ENABLED): WARNING! Found 0 text elements. Tesseract might not be installed correctly or the PDF is empty.")
        else:
            print(f"--- PARSER (OCR ENABLED): Found {len(text_elements)} text elements. ---")

        return text_elements
    except Exception as e:
        print(f"FATAL: Could not parse PDF with OCR. Is Tesseract installed correctly? Error: {e}")
        return []