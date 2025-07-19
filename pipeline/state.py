# pipeline/state.py
from typing import TypedDict, List, Dict, Any

class PipelineState(TypedDict):
    """
    The state for the multimodal pipeline.
    """
    # Input
    pdf_path: str

    # Intermediate data
    page_image_path: str                  # Path to the saved image of the PDF page
    all_text_elements: List[Dict[str, Any]] # Raw OCR data
    llm_structured_output: List[Dict[str, Any]] # The JSON response from the Vision AI

    # Final Output
    values_with_metadata: List[Dict[str, Any]]