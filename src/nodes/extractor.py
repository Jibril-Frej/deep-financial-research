"""Extractor node — identifies the company ticker and filing section from the user's question."""

from typing import Optional

from langchain_core.messages import SystemMessage
from langchain_openai import ChatOpenAI
from pydantic import BaseModel

from graph.state import GraphState
from utils.config import settings
from utils.logging import logger


class ExtractionResult(BaseModel):
    """Structured output for company and section extraction."""

    ticker: str  # Standard stock ticker symbol, e.g. "AAPL"
    section: Optional[str] = None  # "risks", "business", "mnda", or null


llm = ChatOpenAI(model="gpt-4.1-nano", api_key=settings.OPENAI_API_KEY)
structured_llm = llm.with_structured_output(ExtractionResult, method="json_schema")


def extractor_node(state: GraphState):
    """Extracts the company ticker and relevant filing section from the user's question.

    This node runs only when the supervisor has decided to SEARCH.

    Returns:
        dict: ticker and section to be used as Chroma filters in the search node.
    """
    logger.info("--- NODE: EXTRACTING COMPANY & SECTION ---")
    question = state["question"]

    prompt = f"""
    Extract the company and filing section from this financial question: "{question}"

    - ticker: the standard stock ticker symbol (e.g. "AAPL", "NVDA", "MSFT").
    - section: the most relevant SEC filing section, or null if the question spans multiple sections.
      Use ONLY these exact values: "risks", "business", "mnda", or null.
      - "risks"    → risk factors, threats, challenges
      - "business" → what the company does, products, strategy, competition
      - "mnda"     → revenue, profits, financials, management discussion & analysis
      - null       → general questions that do not clearly target one section
    """

    response = structured_llm.invoke([SystemMessage(content=prompt)])
    # Use ticker already set in state (by supervisor's company detection) if available,
    # so a small LLM cannot overwrite a known-correct ticker with a wrong value.
    ticker = state.get("ticker") or response.ticker  # type: ignore[union-attr]
    section = response.section  # type: ignore[union-attr]

    logger.info("Extracted ticker: %s | section: %s", ticker, section)

    return {"ticker": ticker, "section": section}
