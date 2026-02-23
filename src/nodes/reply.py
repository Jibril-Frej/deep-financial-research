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
        dict: A dictionary containing the final response.
    """
    logger.info("--- NODE: GENERATING FINAL REPLY ---")

    question = state["question"]
    context = "\n\n".join(state.get("search_results", []))

    if not context:
        return {
            "final_response": "I'm sorry, I couldn't find any specific information in the SEC filings to answer that question."
        }

    prompt = f"""
    You are a Senior Financial Analyst. Answer the user's question using ONLY the provided SEC filing context.
    
    Guidelines:
    1. If the information is not in the context, state that you don't have enough data.
    2. Use a professional, objective tone.
    3. Cite the company if it's clear from the text.
    4. Use bullet points for readability if listing risks or financial data.
    
    CONTEXT:
    {context}
    
    USER QUESTION:
    {question}
    """

    response = llm.invoke(
        [
            SystemMessage(
                content="You are a helpful assistant that answers based on provided documents."
            ),
            HumanMessage(content=prompt),
        ]
    )

    return {"final_response": response.content}
