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

_UNSUPPORTED_MESSAGE = (
    "This tool currently supports searches about a **single company** at a time. "
    "Queries about multiple companies or entire sectors will be supported in a future update. "
    "Please ask about a specific company (e.g. 'What are Apple's main risks?')."
)


class SupervisorDecision(BaseModel):
    """Defines the structure of the supervisor's decision."""

    next_step: Literal["CLARIFY", "SEARCH", "REJECT", "UNSUPPORTED"]


# Initialize the LLM
llm = ChatOpenAI(model="gpt-4.1-nano", api_key=settings.OPENAI_API_KEY)
structured_llm = llm.with_structured_output(SupervisorDecision, method="json_schema")


def supervisor_node(state: GraphState):
    """Analyzes the user's question and decides the next step in the research graph.

    Returns:
        dict: next_step. For UNSUPPORTED, also sets final_response directly.
    """
    logger.info("--- SUPERVISOR DECIDING PATH ---")
    question = state["question"]

    prompt = f"""
    You are a financial research assistant routing user questions about SEC filings.
    Analyze the question: "{question}"

    Decide the next step:
    1. CLARIFY     — question is too vague or does not mention a specific company.
    2. SEARCH      — question is about the financials of exactly ONE specific company.
    3. REJECT      — question is completely unrelated to finance or SEC filings.
    4. UNSUPPORTED — question asks about MORE THAN ONE company, or about a sector/industry
                     as a whole (e.g. "compare Apple and Microsoft", "how do tech companies...").
    """

    response = structured_llm.invoke([SystemMessage(content=prompt)])
    decision = response.next_step  # type: ignore[union-attr]

    logger.info("Supervisor decision: %s", decision)

    if decision == "UNSUPPORTED":
        return {"next_step": "UNSUPPORTED", "final_response": _UNSUPPORTED_MESSAGE}

    return {"next_step": decision}
