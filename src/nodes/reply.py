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
    search_results = state.get("search_results", [])

    if not search_results:
        return {
            "final_response": "I'm sorry, I couldn't find any specific information in the SEC filings to answer that question."
        }

    # Build context from search results with URLs for inline linking
    context_parts = []
    document_sources = set()
    document_urls = {}  # Track URLs for each ticker
    source_url_map = {}  # Map source descriptions to URLs

    if search_results:
        for result in search_results:
            content = result["content"]
            metadata = result["metadata"]

            # Track sources for links section
            ticker = metadata.get("ticker", "Unknown")
            section = metadata.get("section", "unknown")
            source = metadata.get("source", "Unknown")
            filing_url = metadata.get("filing_url")

            document_sources.add((ticker, section, source))

            # Store URL for this ticker if available
            if filing_url and ticker != "Unknown":
                document_urls[ticker] = filing_url
                # Create a source reference for inline linking
                section_display = section.replace("_", " ").title()
                source_key = f"{ticker}'s {section_display}"
                source_url_map[source_key] = filing_url

            # Add content with enhanced source attribution including URL info
            section_display = section.replace("_", " ").title()
            source_info = f"[Source: {ticker} - {section_display}"
            if filing_url:
                source_info += f" - URL: {filing_url}"
            source_info += "]"

            context_parts.append(f"{source_info}\n{content}")
    else:
        context_parts.append("No relevant information found in the SEC filings.")

    context = "\n\n---\n\n".join(context_parts)

    # Enhanced prompt with instruction to use inline source links
    prompt = f"""
    You are a Senior Financial Analyst. Answer the user's question using ONLY the provided SEC filing context.
    Each piece of context is labeled with its source document and includes the URL to the original SEC filing.
    
    Guidelines:
    1. If the information is not in the context, state that you don't have enough data.
    2. Use a professional, objective tone.
    3. IMPORTANT: When citing information, create inline markdown links to the specific SEC filing.
       Format: "According to [🔗](URL), ..." or "[🔗](URL) indicates...".
    4. Use bullet points for readability if listing risks or financial data.
    5. Extract the URL from the context source information to create proper markdown links.
    6. Always link to the source when mentioning specific information from that source.
    
    CONTEXT:
    {context}
    
    USER QUESTION:
    {question}
    """

    response = llm.invoke(
        [
            SystemMessage(
                content="You are a helpful financial analyst that answers based on provided SEC documents. Create inline markdown links when citing specific sources. Always provide clickable links to the SEC filings when referencing information."
            ),
            HumanMessage(content=prompt),
        ]
    )

    # Combine the main response with additional info
    final_response = response.content

    return {"final_response": final_response}
