# pipeline/state.py
from typing import TypedDict, List, Dict, Any


class PipelineState(TypedDict):
    """
    The state that flows through the pipeline.
    This is like a shared memory between all nodes.
    """
    # Input
    pdf_path: str

    # Intermediate data
    extracted_values: List[Dict[str, Any]]  # The 31 values from extractor
    all_text_elements: List[Dict[str, Any]]  # All text for finding headers

    # Output
    values_with_metadata: List[Dict[str, Any]]  # Final values with headers