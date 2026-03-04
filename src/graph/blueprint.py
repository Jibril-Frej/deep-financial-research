"""This file defines the structure of the LangGraph application.
It sets up the nodes, edges, and conditional logic for our financial research assistant.
"""

from langgraph.graph import END, START, StateGraph

from graph.state import GraphState
from nodes.clarify import clarify_node
from nodes.extractor import extractor_node
from nodes.reply import reply_node
from nodes.search import search_node
from nodes.supervisor import supervisor_node


def route_decision(state: GraphState):
    """Routes to the next node based on the supervisor's decision."""
    decision = state.get("next_step")

    if decision == "SEARCH":
        return "extractor"
    elif decision == "CLARIFY":
        return "clarify"
    elif decision == "REJECT":
        return "reply"
    else:
        return END  # UNSUPPORTED: final_response already set, go straight to END


builder = StateGraph(GraphState)

# Add our nodes
builder.add_node("supervisor", supervisor_node)
builder.add_node("extractor", extractor_node)
builder.add_node("search", search_node)
builder.add_node("reply", reply_node)
builder.add_node("clarify", clarify_node)

# Set the entry point
builder.add_edge(START, "supervisor")

# Define the Conditional Logic
builder.add_conditional_edges(
    "supervisor",
    route_decision,
    {"extractor": "extractor", "clarify": "clarify", "reply": "reply", END: END},
)

# extractor feeds into search, search feeds into reply
builder.add_edge("extractor", "search")
builder.add_edge("search", "reply")
builder.add_edge("reply", END)

# Compile the graph
app = builder.compile()
