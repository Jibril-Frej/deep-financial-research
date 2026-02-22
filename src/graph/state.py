"""Defines the structure of the graph's state."""

from typing import List, Optional, TypedDict


class GraphState(TypedDict):
    """Represents the state of the research graph."""

    question: str  # The user's original query
    reformulated_question: Optional[str]  # The "cleaner" version for the DB
    search_results: List[str]  # Chunks retrieved from ChromaDB
    final_response: Optional[str]  # The actual answer to the user
    next_step: str  # A flag to tell LangGraph where to go next
