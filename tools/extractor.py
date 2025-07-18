# tools/extractor.py
import fitz  # PyMuPDF
import pytesseract
from PIL import Image
import io
import cv2
import numpy as np
import json
import re
import os


def extract_values_from_pdf(pdf_path: str):
    """
    Extracts all numeric table values from the PDF using OCR.
    Returns a list of dictionaries with value, confidence, and bbox.
    """
    try:
        doc = fitz.open(pdf_path)
        page = doc.load_page(0)

        # Render at 2x resolution
        mat = fitz.Matrix(2, 2)
        pix = page.get_pixmap(matrix=mat)
        img_data = pix.tobytes("png")
        pil_img = Image.open(io.BytesIO(img_data))
        doc.close()

        # Convert to grayscale
        gray_img = cv2.cvtColor(np.array(pil_img), cv2.COLOR_RGB2GRAY)

        # Run OCR
        ocr_data = pytesseract.image_to_data(gray_img, output_type=pytesseract.Output.DICT)

        # Extract numeric values
        extracted_values = []
        for i in range(len(ocr_data['text'])):
            text = ocr_data['text'][i].strip()

            # Find numbers in "XX,XX" format
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

        # Sort by position
        extracted_values.sort(key=lambda item: (item['bbox']['y0'], item['bbox']['x0']))

        return extracted_values

    except Exception as e:
        print(f"Error in extract_values_from_pdf: {e}")
        return []


def get_all_text_elements(pdf_path: str):
    """
    Extracts ALL text elements from PDF (not just numeric values).
    Returns a list of all text with positions and confidence.
    """
    try:
        doc = fitz.open(pdf_path)
        page = doc.load_page(0)

        mat = fitz.Matrix(2, 2)
        pix = page.get_pixmap(matrix=mat)
        img_data = pix.tobytes("png")
        pil_img = Image.open(io.BytesIO(img_data))
        doc.close()

        gray_img = cv2.cvtColor(np.array(pil_img), cv2.COLOR_RGB2GRAY)
        ocr_data = pytesseract.image_to_data(gray_img, output_type=pytesseract.Output.DICT)

        all_elements = []
        for i in range(len(ocr_data['text'])):
            text = ocr_data['text'][i].strip()
            if text and int(ocr_data['conf'][i]) > 30:
                all_elements.append({
                    "text": text,
                    "confidence": int(ocr_data['conf'][i]),
                    "bbox": {
                        "x0": ocr_data['left'][i] // 2,
                        "y0": ocr_data['top'][i] // 2,
                        "x1": (ocr_data['left'][i] + ocr_data['width'][i]) // 2,
                        "y1": (ocr_data['top'][i] + ocr_data['height'][i]) // 2
                    }
                })

        return all_elements

    except Exception as e:
        print(f"Error in get_all_text_elements: {e}")
        return []