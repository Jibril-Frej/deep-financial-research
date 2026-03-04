"""
This module defines the search_node function.
"""

from langchain_chroma import Chroma
from langchain_openai import OpenAIEmbeddings

from graph.state import GraphState
from utils.config import settings
from utils.logging import logger


def search_node(state: GraphState):
    """Searches the Chroma database for relevant documents based on the user's question.

    Args:
        state (GraphState): The current state of the graph, containing the user's question.

    Returns:
        dict: A dictionary containing the search results with text content and metadata.
    """

    logger.info("--- NODE: SEARCHING CHROMA DATABASE  ---")

    # 1. Initialize Embeddings (Must match the ones used for indexing)
    embeddings = OpenAIEmbeddings(model="text-embedding-3-small", api_key=settings.OPENAI_API_KEY)

    # 2. Connect to the existing Vector Store
    vector_db = Chroma(
        persist_directory=str(settings.INDEX_DIR),
        embedding_function=embeddings,
        collection_name="sec_filings",
    )

    # 3. Build metadata filter from extracted ticker / section
    ticker = state.get("ticker")
    section = state.get("section")

    if ticker and section:
        where = {"$and": [{"ticker": {"$eq": ticker}}, {"section": {"$eq": section}}]}
    elif ticker:
        where = {"ticker": {"$eq": ticker}}
    else:
        where = None

    logger.info("Search filter: %s", where)

    # 4. Perform filtered vector search (top 5 most similar chunks)
    docs = vector_db.similarity_search(
        query=state["question"],
        k=5,
        filter=where,
    )

    # 4. Extract text and metadata from the Document objects
    retrieved_texts = []
    search_results = []

    for i, doc in enumerate(docs):
        logger.info("Chunk %d Source: %s", i + 1, doc.metadata.get("source", "Unknown"))
        logger.info("Chunk %d Content Preview: %s", i + 1, doc.page_content[:200])

        # Keep backward compatibility
        retrieved_texts.append(doc.page_content)

        # Add enhanced results with metadata
        search_results.append({"content": doc.page_content, "metadata": doc.metadata})

    logger.info("Retrieved %d chunks directly from ChromaDB.", len(retrieved_texts))

    return {
        "search_results": search_results,
    }
