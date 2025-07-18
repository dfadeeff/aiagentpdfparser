# pdf_parser.py
import fitz  # PyMuPDF
import pytesseract
from PIL import Image, ImageEnhance, ImageFilter
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
        # Use higher DPI for better quality
        mat = fitz.Matrix(3, 3)  # 3x scale factor
        pix = page.get_pixmap(matrix=mat)
        doc.close()

        img_bytes = pix.tobytes("png")
        pil_image = Image.open(io.BytesIO(img_bytes))

        # Enhance image for better OCR
        # Convert to grayscale
        pil_gray = pil_image.convert('L')

        # Enhance contrast
        enhancer = ImageEnhance.Contrast(pil_gray)
        pil_enhanced = enhancer.enhance(2.0)

        # Apply slight blur to reduce noise
        pil_enhanced = pil_enhanced.filter(ImageFilter.MedianFilter(size=3))

        # Convert to numpy array for OpenCV processing
        cv_image = cv2.cvtColor(np.array(pil_image), cv2.COLOR_RGB2BGR)

        # Extract Text Blocks using multiple OCR configurations
        text_elements = []
        seen_texts = set()  # To avoid duplicates

        # Try different OCR configurations
        configs = [
            r'--oem 3 --psm 6',  # Uniform block of text
            r'--oem 3 --psm 11',  # Sparse text
            r'--oem 3 --psm 12',  # Sparse text with OSD
        ]

        for config in configs:
            try:
                ocr_data = pytesseract.image_to_data(pil_enhanced, output_type=pytesseract.Output.DICT, config=config)

                for i in range(len(ocr_data['text'])):
                    confidence = int(ocr_data['conf'][i])
                    text = ocr_data['text'][i].strip()

                    # Very low confidence threshold to catch everything
                    if confidence > -1 and text and text not in ['|', '-', '']:  # Accept even negative confidence
                        x0 = ocr_data['left'][i] // 3  # Scale back due to 3x magnification
                        y0 = ocr_data['top'][i] // 3
                        x1 = (ocr_data['left'][i] + ocr_data['width'][i]) // 3
                        y1 = (ocr_data['top'][i] + ocr_data['height'][i]) // 3

                        # Create unique key for deduplication
                        key = f"{text}_{x0}_{y0}"

                        if key not in seen_texts:
                            seen_texts.add(key)

                            # Handle concatenated text
                            if '.' in text and 'Row' in text:
                                # Split "Row.Invisible.Grid1" type texts
                                parts = text.split('.')
                                for j, part in enumerate(parts):
                                    if part.strip():
                                        text_elements.append({
                                            "content": part.strip(),
                                            "bbox": (x0 + j * 20, y0, x1, y1)
                                        })
                            else:
                                text_elements.append({
                                    "content": text,
                                    "bbox": (x0, y0, x1, y1)
                                })
            except Exception as e:
                print(f"OCR config {config} failed: {e}")
                continue

        # Also try PyMuPDF's text extraction as fallback
        doc = fitz.open(pdf_path)
        page = doc.load_page(0)

        # Get text with positions
        blocks = page.get_text("dict")

        for block in blocks["blocks"]:
            if "lines" in block:
                for line in block["lines"]:
                    for span in line["spans"]:
                        text = span["text"].strip()
                        if text and text not in ['|', '-', '']:
                            bbox = span["bbox"]
                            key = f"{text}_{int(bbox[0])}_{int(bbox[1])}"

                            if key not in seen_texts:
                                seen_texts.add(key)
                                text_elements.append({
                                    "content": text,
                                    "bbox": (bbox[0], bbox[1], bbox[2], bbox[3])
                                })

        doc.close()

        # Sort text elements by position (top to bottom, left to right)
        text_elements.sort(key=lambda x: (x['bbox'][1], x['bbox'][0]))

        print(f"--- PARSER: Found {len(text_elements)} text elements ---")

        # Extract Lines using OpenCV
        gray = cv2.cvtColor(cv_image, cv2.COLOR_BGR2GRAY)

        # Use better thresholding
        _, binary = cv2.threshold(gray, 200, 255, cv2.THRESH_BINARY_INV)

        # Detect horizontal lines
        horiz_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (50, 1))
        detected_horiz = cv2.morphologyEx(binary, cv2.MORPH_OPEN, horiz_kernel, iterations=2)
        horiz_lines = []
        contours, _ = cv2.findContours(detected_horiz, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        for c in contours:
            x, y, w, h = cv2.boundingRect(c)
            if w > 30:  # Filter out small lines
                horiz_lines.append((x, y, x + w, y))

        # Detect vertical lines
        vert_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (1, 50))
        detected_vert = cv2.morphologyEx(binary, cv2.MORPH_OPEN, vert_kernel, iterations=2)
        vert_lines = []
        contours, _ = cv2.findContours(detected_vert, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        for c in contours:
            x, y, w, h = cv2.boundingRect(c)
            if h > 30:  # Filter out small lines
                vert_lines.append((x, y, x, y + h))

        print(f"--- PARSER: Found {len(horiz_lines)} horizontal and {len(vert_lines)} vertical lines ---")

        return text_elements, horiz_lines, vert_lines

    except Exception as e:
        print(f"ERROR: Could not parse PDF. Error: {e}")
        import traceback
        traceback.print_exc()
        return [], [], []