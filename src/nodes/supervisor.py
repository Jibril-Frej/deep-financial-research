"""Supervisor node for the research graph"""

import warnings
from typing import Literal

from langchain_core.messages import SystemMessage
from langchain_openai import ChatOpenAI
from pydantic import BaseModel

from graph.state import GraphState
from utils.config import settings
from utils.logging import logger

# Filter out the specific Pydantic serialization warning
warnings.filterwarnings(
    "ignore", category=UserWarning, message=".*Pydantic serializer warnings:.*"
)


class SupervisorDecision(BaseModel):
    """Defines the structure of the supervisor's decision."""

    next_step: Literal["CLARIFY", "SEARCH", "REJECT"]


# Initialize the LLM
llm = ChatOpenAI(model="gpt-4.1-nano", api_key=settings.OPENAI_API_KEY)
structured_llm = llm.with_structured_output(SupervisorDecision, method="json_schema")


def supervisor_node(state: GraphState):
    """Analyzes the user's question and decides the next step in the research graph.

    Args:
        state (GraphState): The current state of the research graph..

    Returns:
        dict: A dictionary containing the next step in the research graph.
    """
    logger.info("--- SUPERVISOR DECIDING PATH ---")
    question = state["question"]

    prompt = f"""
    You are a financial research assistant. Analyze the user's question: "{question}"
    
    Decide the next step:
    1. If the question is vague, or is not a specific financial question, return: 'CLARIFY'
    2. If the question is about the financials of a specific company (either NVDA or AAPL), return: 'SEARCH'
    3. If the question is unrelated to finance or is a company we do not have, return: 'REJECT'
    
    Respond with ONLY one word: CLARIFY, SEARCH, or REJECT.
    """

    response = structured_llm.invoke([SystemMessage(content=prompt)])
    decision = response.next_step  # type: ignore[union-attr]

    logger.info("Supervisor decision: %s", decision)

    return {"next_step": decision}
