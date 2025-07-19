# pipeline/graph.py
from langgraph.graph import StateGraph, END
from pipeline.state import PipelineState
from pipeline.nodes import context_gathering_node, multimodal_reasoning_node, final_structuring_node

def create_pipeline():
    """
    Creates the LangGraph pipeline with a powerful multimodal reasoning node.
    """
    workflow = StateGraph(PipelineState)

    # Define the new, working nodes
    workflow.add_node("gather_context", context_gathering_node)
    workflow.add_node("reason_with_vision", multimodal_reasoning_node)
    workflow.add_node("structure_final_output", final_structuring_node)

    # Define the flow
    workflow.set_entry_point("gather_context")
    workflow.add_edge("gather_context", "reason_with_vision")
    workflow.add_edge("reason_with_vision", "structure_final_output")
    workflow.add_edge("structure_final_output", END)

    return workflow.compile()