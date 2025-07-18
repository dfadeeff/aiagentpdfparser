# pipeline/graph.py
from langgraph.graph import StateGraph, END
from pipeline.state import PipelineState
from pipeline.nodes import extraction_node, metadata_enrichment_node, cleaning_node


def create_pipeline():
    """
    Creates the LangGraph pipeline.
    This defines HOW data flows through the nodes.
    """
    # Create the graph with our state type
    workflow = StateGraph(PipelineState)

    # Add all nodes
    workflow.add_node("extract", extraction_node)
    workflow.add_node("enrich", metadata_enrichment_node)
    workflow.add_node("clean", cleaning_node)

    # Define the flow
    workflow.set_entry_point("extract")
    workflow.add_edge("extract", "enrich")
    workflow.add_edge("enrich", "clean")
    workflow.add_edge("clean", END)

    # Compile and return
    return workflow.compile()