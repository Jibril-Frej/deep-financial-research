from langchain_core.messages import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI

from graph.state import GraphState
from utils.config import settings
from utils.logging import logger

# Initialize the LLM
llm = ChatOpenAI(model="gpt-4.1-nano", api_key=settings.OPENAI_API_KEY)


def reply_node(state: GraphState):
    """Replies to the user's question based on the retrieved search results from ChromaDB.

    Args:
        state (GraphState): The current state of the graph.

    Returns:
        dict: A dictionary containing the final response with document links.
    """
    logger.info("--- NODE: GENERATING FINAL REPLY ---")

    question = state["question"]

    # Use enhanced search results with metadata if available, otherwise fall back to basic text
    search_results_with_metadata = state.get("search_results_with_metadata", [])
    basic_search_results = state.get("search_results", [])

    if not search_results_with_metadata and not basic_search_results:
        return {
            "final_response": "I'm sorry, I couldn't find any specific information in the SEC filings to answer that question."
        }

    # Build context from search results
    context_parts = []
    document_sources = set()

    if search_results_with_metadata:
        for i, result in enumerate(search_results_with_metadata):
            content = result["content"]
            metadata = result["metadata"]

            # Track sources for links section
            ticker = metadata.get("ticker", "Unknown")
            section = metadata.get("section", "unknown")
            source = metadata.get("source", "Unknown")
            document_sources.add((ticker, section, source))

            # Add content with source attribution
            context_parts.append(
                f"[Source: {ticker} - {section.replace('_', ' ').title()}]\n{content}"
            )
    else:
        # Fallback to basic search results
        context_parts = basic_search_results

    context = "\n\n---\n\n".join(context_parts)

    # Create document links section
    document_links_section = ""
    if document_sources:
        document_links_section = "\n\n**📄 Sources Referenced:**\n"
        for ticker, section, source in sorted(document_sources):
            # Format section name for display
            section_display = section.replace("_", " ").title()
            document_links_section += f"- **{ticker}** - {section_display} (from {source})\n"

    # Enhanced prompt with instruction to reference sources
    prompt = f"""
    You are a Senior Financial Analyst. Answer the user's question using ONLY the provided SEC filing context.
    Each piece of context is labeled with its source document.
    
    Guidelines:
    1. If the information is not in the context, state that you don't have enough data.
    2. Use a professional, objective tone.
    3. Cite the company and document section when referencing specific information.
    4. Use bullet points for readability if listing risks or financial data.
    5. When citing information, reference the source (e.g., "According to Apple's Business section..." or "NVIDIA's Risk Factors indicate...").
    
    CONTEXT:
    {context}
    
    USER QUESTION:
    {question}
    """

    response = llm.invoke(
        [
            SystemMessage(
                content="You are a helpful assistant that answers based on provided documents. Always cite your sources when possible."
            ),
            HumanMessage(content=prompt),
        ]
    )

    # Combine the main response with document links
    final_response = response.content + document_links_section

    return {"final_response": final_response}
