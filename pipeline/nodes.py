# pipeline/nodes.py - FIXED HYBRID APPROACH
import base64
import json
import os
import re
from typing import Dict, List, Any

try:
    from openai import OpenAI

    client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))
except ImportError:
    print("FATAL ERROR: The 'openai' library is not installed.")
    client = None
except Exception:
    print("FATAL ERROR: OPENAI_API_KEY environment variable not set.")
    client = None

from pipeline.state import PipelineState
from tools.extractor import get_all_text_elements


def encode_image_to_base64(image_path: str) -> str:
    """Encodes an image file to a base64 string for the API call."""
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode('utf-8')


def context_gathering_node(state: PipelineState) -> Dict[str, Any]:
    """
    NODE 1: OCR + Image preparation
    """
    print("\n🧠 NODE 1: OCR + IMAGE PREPARATION")
    print("-" * 40)
    pdf_path = state["pdf_path"]
    all_elements = get_all_text_elements(pdf_path)

    import fitz
    doc = fitz.open(pdf_path)
    page = doc.load_page(0)
    pix = page.get_pixmap(matrix=fitz.Matrix(3, 3))
    output_image_path = "output/page_image.png"
    os.makedirs("output", exist_ok=True)
    pix.save(output_image_path)
    doc.close()

    print(f"✅ Extracted {len(all_elements)} text elements and saved page image.")
    return {"all_text_elements": all_elements, "page_image_path": output_image_path}


def multimodal_reasoning_node(state: PipelineState) -> Dict[str, Any]:
    """
    NODE 2: FIXED Vision AI prompt for 34 values
    """
    print("\n🤖 NODE 2: VISION AI STRUCTURE ANALYSIS")
    print("-" * 40)

    if not client:
        raise ConnectionError("OpenAI client not initialized.")

    image_path = state["page_image_path"]
    base64_image = encode_image_to_base64(image_path)

    prompt = """
    Extract ALL 34 values from this table with their hierarchical structure.

    **WHAT TO EXTRACT (34 total):**
    - 31 numerical values in XX,XX format
    - 3 text values: DD (in M1/Col5), EE (in M2/Col5), FF (in M4/Col5)

    **TABLE STRUCTURE:**
    - Col1: Simple column
    - Col2: Split into Col2A/Col3A (left) and Col2B/Col3B (right)
    - Col4: Split into Col4A (left) and Col4B (right)  
    - Col5: Simple column (contains DD, EE, FF)

    **ROW STRUCTURE:**
    - M1/Merged1: AA, BB, CC sub-rows
    - M2/Merged2: Single row
    - M4: Merged4 and Merged5 rows

    **JSON OUTPUT:**
    Return {"values": [array of 34 objects]} where each object has:
    - "value": exact content
    - "row_headers": [hierarchy from outer to inner]
    - "column_headers": [hierarchy from outer to inner]

    **CRITICAL FIXES:**
    1. Values 50,00 and 54,00 need COMPLETE row headers: ["M1","Merged1","Row.Invisible.Grid1","AA"]
    2. Values 35,00 are under Col2 section, NOT Col4
    3. Don't miss DD, EE, FF in the rightmost column
    4. Return exactly 34 values total

    Analyze systematically and return complete structure.
    """

    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "user", "content": [
                    {"type": "text", "text": prompt},
                    {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{base64_image}"}},
                ]},
            ],
            response_format={"type": "json_object"},
            temperature=0.0
        )
        llm_output = json.loads(response.choices[0].message.content)
        values = llm_output.get("values", [])

        if len(values) != 34:
            print(f"⚠️ Expected 34, got {len(values)}. Retrying...")
            correction_prompt = "You must find exactly 34 values: 31 numbers + DD + EE + FF. Reanalyze completely."

            response = client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "user", "content": [
                        {"type": "text", "text": correction_prompt},
                        {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{base64_image}"}},
                    ]},
                ],
                response_format={"type": "json_object"},
                temperature=0.0
            )
            llm_output = json.loads(response.choices[0].message.content)
            values = llm_output.get("values", [])

        print(f"✅ AI found {len(values)} values with structure.")
        return {"llm_structured_output": values}

    except Exception as e:
        print(f"❌ AI analysis failed: {e}")
        return {"llm_structured_output": []}


def final_structuring_node(state: PipelineState) -> Dict[str, Any]:
    """
    NODE 3: FIXED OCR merging for all 34 values
    """
    print("\n🧩 NODE 3: MERGING AI + OCR (FIXED)")
    print("-" * 40)

    llm_data = state["llm_structured_output"]
    ocr_data = state["all_text_elements"]

    # FIXED: Include both numerical AND text values
    ocr_values = [elem for elem in ocr_data if
                  re.match(r'^\d{1,4},\d{2}$', elem["text"]) or
                  elem["text"] in ["DD", "EE", "FF"]]

    print(f"📊 AI: {len(llm_data)} values")
    print(f"📊 OCR: {len(ocr_values)} values")

    # Sort OCR by position
    ocr_values.sort(key=lambda x: (x['bbox']['y0'], x['bbox']['x0']))

    final_results = []
    available_ocr = list(ocr_values)

    # Match AI structure with OCR coordinates
    for llm_item in llm_data:
        matched = False
        for i, ocr_item in enumerate(available_ocr):
            if llm_item["value"] == ocr_item["text"]:
                final_results.append({
                    "value": llm_item["value"],
                    "row_headers": llm_item.get("row_headers", []),
                    "column_headers": llm_item.get("column_headers", []),
                    "confidence": ocr_item.get("confidence"),
                    "bbox": ocr_item.get("bbox")
                })
                del available_ocr[i]
                matched = True
                break

        if not matched:
            print(f"⚠️ No OCR match for: {llm_item['value']}")

    # Handle unmatched OCR values
    for remaining in available_ocr:
        final_results.append({
            "value": remaining["text"],
            "row_headers": ["Unknown"],
            "column_headers": ["Unknown"],
            "confidence": remaining.get("confidence"),
            "bbox": remaining.get("bbox")
        })

    # Sort by position
    final_results.sort(key=lambda x: (x['bbox']['y0'], x['bbox']['x0']))

    # Validation
    text_values = [v["value"] for v in final_results if v["value"] in ["DD", "EE", "FF"]]
    print(f"✅ Final: {len(final_results)} values")
    print(f"📝 Text values found: {text_values}")

    return {"values_with_metadata": final_results}