"""Supervisor node for the research graph"""

import warnings
from typing import Literal

from langchain_core.messages import SystemMessage
from langchain_openai import ChatOpenAI
from pydantic import BaseModel

from graph.state import GraphState
from utils.config import settings
from utils.logging import logger
from utils.sp500 import find_sp500_mentions

# Filter out the specific Pydantic serialization warning
warnings.filterwarnings(
    "ignore", category=UserWarning, message=".*Pydantic serializer warnings:.*"
)

_UNSUPPORTED_MESSAGE = (
    "This tool currently supports searches about a **single company** in the S&P 500 at a time. "
    "Queries about multiple companies or entire sectors will be supported in a future update. "
    "Please ask about a specific company (e.g. 'What are Apple's main risks?')."
)


class SupervisorDecision(BaseModel):
    """Defines the structure of the supervisor's decision."""

    next_step: Literal["CLARIFY", "SEARCH", "REJECT", "UNSUPPORTED"]


# Initialize the LLM
llm = ChatOpenAI(model="gpt-4.1-nano", api_key=settings.OPENAI_API_KEY)
structured_llm = llm.with_structured_output(SupervisorDecision, method="json_schema")


def supervisor_node(state: GraphState) -> dict:
    """Analyzes the user's question and decides the next step in the research graph.

    Company detection via find_sp500_mentions() constrains the LLM's allowed decisions:
    - 2+ companies → UNSUPPORTED immediately (no LLM call)
    - 1 company    → LLM chooses between SEARCH or CLARIFY
    - 0 companies  → LLM chooses between CLARIFY, REJECT, or UNSUPPORTED

    Returns:
        dict: next_step. For UNSUPPORTED, also sets final_response directly.
    """
    logger.info("--- SUPERVISOR DECIDING PATH ---")
    question = state["question"]

    matched_tickers = find_sp500_mentions(question)
    match_count = len(matched_tickers)
    logger.info("S&P 500 company mentions detected: %s", matched_tickers)

    # Short-circuit: multiple companies detected — no LLM needed
    if match_count >= 2:
        logger.info("Supervisor decision: UNSUPPORTED (multiple companies detected)")
        return {"next_step": "UNSUPPORTED", "final_response": _UNSUPPORTED_MESSAGE}

    if match_count == 1:
        prompt = f"""
        You are a financial research assistant routing user questions about SEC filings.
        Analyze the question: "{question}"

        The question mentions exactly one S&P 500 company. Choose between:

        1. SEARCH  — the question is clear enough to search (asks about financials, risks,
                     business, or strategy of the identified company).
                     Example: "What are Airbnb's main risk factors?"

        2. CLARIFY — the question mentions the company but is too vague to search meaningfully.
                     Example: "Tell me about Airbnb" (no specific financial topic)
        """
    else:
        prompt = f"""
        You are a financial research assistant routing user questions about SEC filings.
        Analyze the question: "{question}"

        No S&P 500 company was identified in the question. Choose between:

        1. REJECT      — the question has nothing to do with finance, business, or SEC filings.
                         Example: "What is the weather today?"

        2. UNSUPPORTED — the question is finance-related but refers to a non-S&P 500 entity
                         (private company, university, government body, non-US company, or a
                         sector/industry as a whole).
                         Examples: "Harvard University risks", "how do tech companies discuss AI?"

        3. CLARIFY     — the question is about finance/business but does not mention any specific
                         company (too vague to search).
                         Example: "What are the main risks?" (no company mentioned)
        """

    response = structured_llm.invoke([SystemMessage(content=prompt)])
    decision = response.next_step  # type: ignore[union-attr]

    logger.info("Supervisor decision: %s", decision)

    if decision == "UNSUPPORTED":
        return {"next_step": "UNSUPPORTED", "final_response": _UNSUPPORTED_MESSAGE}

    return {"next_step": decision}
