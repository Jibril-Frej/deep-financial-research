from langchain_core.messages import SystemMessage
from langchain_openai import ChatOpenAI

from graph.state import GraphState
from utils.config import settings
from utils.logging import logger

llm = ChatOpenAI(model="gpt-4.1-mini", api_key=settings.OPENAI_API_KEY)


def clarify_node(state: GraphState):
    """This node is triggered when the supervisor determines that the user's question is too vague to answer directly.

    Args:
        state (GraphState): The current state of the graph.

    Returns:
        dict: A dictionary containing the clarification response.
    """
    logger.info("--- NODE: ASKING FOR CLARIFICATION ---")

    question = state["question"]

    prompt = f"""
    The user asked: "{question}"
    
    As a financial assistant, you are currently unable to answer this because it is too vague.
    Please ask a follow-up question to help the user. 
    Common issues:
    - They didn't mention a specific company (NVDA or AAPL).
    - They did not ask about a specific financial metric (revenue, profit, etc.).
    - They asked a non-financial question.
    - They used ambiguous language that could refer to multiple things.
    
    Keep your response brief and helpful.
    """

    response = llm.invoke([SystemMessage(content=prompt)])

    # We put the clarification into 'final_response' because this is
    # the end of the current graph run.
    return {"final_response": response.content}
