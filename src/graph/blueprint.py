"""This file defines the structure of the LangGraph application.
It sets up the nodes, edges, and conditional logic for our financial research assistant.
"""

from langgraph.graph import END, START, StateGraph

from graph.state import GraphState
from nodes.search import search_node
from nodes.supervisor import supervisor_node
from utils.logging import logger


def reply_node(state: GraphState):
    logger.info("--- NODE: GENERATING FINAL REPLY ---")
    # We'll use the LLM to write a nice answer later
    return {"final_response": "Here is what I found in the documents..."}


# 2. Define the Routing Logic
def route_decision(state: GraphState):
    """
    This function looks at the 'next_step' in the state
    and tells LangGraph which string (node name) to go to next.
    """
    decision = state.get("next_step")

    if decision == "SEARCH":
        return "search"
    elif decision == "CLARIFY":
        return "reply"  # For now, just reply with a clarification request
    else:
        return END


# 3. Build the Graph
builder = StateGraph(GraphState)

# Add our nodes
builder.add_node("supervisor", supervisor_node)
builder.add_node("search", search_node)
builder.add_node("reply", reply_node)

# Set the entry point
builder.add_edge(START, "supervisor")

# Define the Conditional Logic
builder.add_conditional_edges(
    "supervisor", route_decision, {"search": "search", "reply": "reply", "end": END}
)

# Connect the search result back to a reply
builder.add_edge("search", "reply")
builder.add_edge("reply", END)

# Compile the graph
app = builder.compile()
