# pipeline/state.py
from typing import TypedDict, List, Dict, Any

class PipelineState(TypedDict):
    """
    The state for the multimodal pipeline with spatial enhancement.
    """
    # Input
    pdf_path: str

    # Intermediate data
    page_image_path: str                    # Path to the saved image of the PDF page
    all_text_elements: List[Dict[str, Any]] # Raw OCR data
    target_values: List[Dict[str, Any]]     # Filtered target values (numbers + DD/EE/FF)
    spatial_hints: List[str]                # Spatial coordinate hints for AI
    table_structure: Dict[str, Any]         # Dynamic table structure analysis
    llm_structured_output: List[Dict[str, Any]] # The JSON response from the Vision AI

    # Final Output
    values_with_metadata: List[Dict[str, Any]]