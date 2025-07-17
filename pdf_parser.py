# pdf_parser.py
import fitz  # PyMuPDF
import pytesseract
from PIL import Image
import io
import cv2
import numpy as np
from typing import List, Dict, Any, Tuple


def extract_all_elements(pdf_path: str) -> Tuple[List[Dict[str, Any]], List[Tuple], List[Tuple]]:
    """
    Opens a PDF, converts it to an image, and extracts:
    1. Text blocks with content and coordinates
    2. Horizontal line segments
    3. Vertical line segments
    """
    print(f"--- PARSER: Reading text and lines from: {pdf_path} ---")

    try:
        # Render PDF page as high-quality image
        doc = fitz.open(pdf_path)
        page = doc.load_page(0)
        pix = page.get_pixmap(dpi=300)
        doc.close()

        img_bytes = pix.tobytes("png")
        pil_image = Image.open(io.BytesIO(img_bytes))
        cv_image = cv2.cvtColor(np.array(pil_image), cv2.COLOR_RGB2BGR)

        # Extract Text Blocks using Pytesseract
        text_elements = []
        ocr_data = pytesseract.image_to_data(pil_image, output_type=pytesseract.Output.DICT)

        for i in range(len(ocr_data['text'])):
            confidence = int(ocr_data['conf'][i])
            text = ocr_data['text'][i].strip()

            # Lower confidence threshold to catch more text
            if confidence > 30 and text:
                x0 = ocr_data['left'][i]
                y0 = ocr_data['top'][i]
                x1 = x0 + ocr_data['width'][i]
                y1 = y0 + ocr_data['height'][i]
                text_elements.append({
                    "content": text,
                    "bbox": (x0, y0, x1, y1)
                })

        print(f"--- PARSER: Found {len(text_elements)} text elements ---")

        # Extract Lines using OpenCV
        gray = cv2.cvtColor(cv_image, cv2.COLOR_BGR2GRAY)
        binary = cv2.adaptiveThreshold(~gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                                       cv2.THRESH_BINARY, 15, -2)

        # Detect horizontal lines
        horiz_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (80, 1))
        detected_horiz = cv2.morphologyEx(binary, cv2.MORPH_OPEN, horiz_kernel, iterations=2)
        horiz_lines = []
        contours, _ = cv2.findContours(detected_horiz, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        for c in contours:
            x, y, w, h = cv2.boundingRect(c)
            if w > 30:  # Filter out small lines
                horiz_lines.append((x, y, x + w, y))

        # Detect vertical lines
        vert_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (1, 80))
        detected_vert = cv2.morphologyEx(binary, cv2.MORPH_OPEN, vert_kernel, iterations=2)
        vert_lines = []
        contours, _ = cv2.findContours(detected_vert, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        for c in contours:
            x, y, w, h = cv2.boundingRect(c)
            if h > 50:  # Filter out small lines
                vert_lines.append((x, y, x, y + h))

        print(f"--- PARSER: Found {len(horiz_lines)} horizontal and {len(vert_lines)} vertical lines ---")

        return text_elements, horiz_lines, vert_lines

    except Exception as e:
        print(f"ERROR: Could not parse PDF. Error: {e}")
        return [], [], []