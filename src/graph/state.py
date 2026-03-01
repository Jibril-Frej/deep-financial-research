"""Defines the structure of the graph's state."""

from typing import Dict, List, Optional, TypedDict


class DocumentChunk(TypedDict):
    """Represents a document chunk with its metadata."""
    
    content: str  # The actual text content
    metadata: Dict[str, str]  # Document metadata (ticker, section, source, etc.)


class GraphState(TypedDict):
    """Represents the state of the research graph."""

    question: str  # The user's original query
    reformulated_question: Optional[str]  # The "cleaner" version for the DB
    search_results: List[str]  # Chunks retrieved from ChromaDB (for backward compatibility)
    search_results_with_metadata: Optional[List[DocumentChunk]]  # Enhanced search results with metadata
    final_response: Optional[str]  # The actual answer to the user
    next_step: str  # A flag to tell LangGraph where to go next
