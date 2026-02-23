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
        dict: A dictionary containing the search results.
    """

    logger.info("--- NODE: SEARCHING CHROMA DATABASE  ---")

    # 1. Initialize Embeddings (Must match the ones used for indexing)
    embeddings = OpenAIEmbeddings(model="text-embedding-3-large", api_key=settings.OPENAI_API_KEY)

    # 2. Connect to the existing Vector Store
    vector_db = Chroma(
        persist_directory=str(settings.INDEX_DIR),
        embedding_function=embeddings,
        collection_name="sec_filings",
    )

    # 3. Perform Direct Vector Search
    # We look for the top 5 most similar chunks
    docs = vector_db.similarity_search(
        query=state["question"],
        k=5,
    )

    # 4. Extract text from the Document objects
    retrieved_texts = []
    for i, doc in enumerate(docs):
        logger.info("Chunk %d Source: %s", i + 1, doc.metadata.get("source", "Unknown"))
        logger.info("Chunk %d Content Preview: %s", i + 1, doc.page_content[:200])
        retrieved_texts.append(doc.page_content)

    logger.info("Retrieved %d chunks directly from ChromaDB.", len(retrieved_texts))

    return {"search_results": retrieved_texts}
