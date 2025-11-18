from langgraph.graph import StateGraph, END
from .state import SummarizationState
from .nodes import summarize_node

# Define the graph
builder = StateGraph(SummarizationState)

# Add the summarize node
builder.add_node("summarize", summarize_node)

# Set the entry point
builder.set_entry_point("summarize")

# The summarize node is the final step in this sub-graph
builder.add_edge("summarize", END)

# Compile the graph
app = builder.compile()
