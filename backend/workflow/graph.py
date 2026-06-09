"""Langgraph workflow compilation and graph setup"""
from langgraph.graph import StateGraph
from workflow.state import TroubleshootState
from workflow.nodes import (
    parse_error_node,
    search_confluence_node,
    search_tavily_node,
    generate_response_node
)


def build_workflow():
    """Build and compile the Langgraph workflow"""
    
    workflow = StateGraph(TroubleshootState)
    
    # Add nodes
    workflow.add_node("parse_error", parse_error_node)
    workflow.add_node("search_confluence", search_confluence_node)
    workflow.add_node("search_tavily", search_tavily_node)
    workflow.add_node("generate_response", generate_response_node)
    
    # Define edges (workflow flow)
    workflow.add_edge("parse_error", "search_confluence")
    workflow.add_edge("search_confluence", "search_tavily")
    workflow.add_edge("search_tavily", "generate_response")
    
    # Set entry and finish points
    workflow.set_entry_point("parse_error")
    workflow.set_finish_point("generate_response")
    
    # Compile the graph
    graph = workflow.compile()
    return graph


# Create singleton graph instance
graph = build_workflow()
