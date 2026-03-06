"""Supervisor node for the research graph"""

import warnings
from typing import Literal

from langchain_core.messages import SystemMessage
from langchain_openai import ChatOpenAI
from pydantic import BaseModel

from graph.state import GraphState
from utils.config import settings
from utils.logging import logger
from utils.sp500 import find_sp500_candidates

# Filter out the specific Pydantic serialization warning
warnings.filterwarnings(
    "ignore", category=UserWarning, message=".*Pydantic serializer warnings:.*"
)

_UNSUPPORTED_MESSAGE = (
    "This tool currently supports searches about a **single company** in the S&P 500 at a time. "
    "Queries about multiple companies or entire sectors will be supported in a future update. "
    "Please ask about a specific company (e.g. 'What are Apple's main risks?')."
)


class _SingleCompanyDecision(BaseModel):
    """Used when exactly one S&P 500 company is detected. UNSUPPORTED is structurally excluded."""

    next_step: Literal["SEARCH", "CLARIFY", "REJECT"]


class _NoCompanyDecision(BaseModel):
    """Used when no S&P 500 company is detected."""

    next_step: Literal["SEARCH", "CLARIFY", "REJECT", "UNSUPPORTED"]


class _VerifierDecision(BaseModel):
    """Used to disambiguate candidate companies found in the query.

    ticker must be one of the candidate tickers, "MULTIPLE" (query asks about
    more than one company), or "NONE" (no candidate is the subject of the query).
    """

    ticker: str


# Initialize the LLM
_llm = ChatOpenAI(model="gpt-4.1-nano", api_key=settings.OPENAI_API_KEY)
_single_company_llm = _llm.with_structured_output(_SingleCompanyDecision, method="json_schema")
_no_company_llm = _llm.with_structured_output(_NoCompanyDecision, method="json_schema")
_verifier_llm = _llm.with_structured_output(_VerifierDecision, method="json_schema")


def _verify_company(question: str, candidates: list[tuple[str, str]]) -> str | None:
    """Asks the LLM to confirm which candidate company (if any) the question is about.

    Args:
        question: The raw user question.
        candidates: List of (ticker, company_name) pairs from find_sp500_candidates.

    Returns:
        A ticker string if one company is confirmed, "MULTIPLE" if the question
        asks about more than one company, or None if no candidate is the subject.
    """
    valid_tickers = {ticker for ticker, _ in candidates}
    candidate_list = "\n".join(f"- {name} (ticker: {ticker})" for ticker, name in candidates)

    prompt = f"""
    The following S&P 500 companies were found as potential matches in the question below.
    Identify which ONE company the user is asking about.

    Question: "{question}"

    Candidates:
    {candidate_list}

    Reply with:
    - The ticker of the single company being asked about (e.g. "META")
    - "MULTIPLE" if the question is clearly about more than one of these companies
    - "NONE" if none of these companies are the actual subject of the question
    """

    response = _verifier_llm.invoke([SystemMessage(content=prompt)])
    result = response.ticker  # type: ignore[union-attr]

    if result == "MULTIPLE":
        return "MULTIPLE"
    if result in valid_tickers:
        return result
    return None


def supervisor_node(state: GraphState) -> dict:
    """Analyzes the user's question and decides the next step in the research graph.

    Uses a two-step company detection approach:
    1. find_sp500_candidates() generates word-level candidate matches (may have false positives)
    2. _verify_company() uses an LLM to confirm which candidate (if any) is the subject

    Routing based on verification result:
    - MULTIPLE confirmed companies → UNSUPPORTED immediately
    - 1 confirmed company          → LLM constrained to SEARCH, CLARIFY, or REJECT
    - 0 confirmed (no candidates or verifier returned NONE) → LLM with full options

    Returns:
        dict: next_step. For UNSUPPORTED, also sets final_response directly.
    """
    logger.info("--- SUPERVISOR DECIDING PATH ---")
    question = state["question"]

    candidates = find_sp500_candidates(question)
    logger.info("S&P 500 candidates detected: %s", [(t, n) for t, n in candidates])

    verified_ticker: str | None = None
    if candidates:
        verified_ticker = _verify_company(question, candidates)
        logger.info("Verifier result: %s", verified_ticker)

    # Short-circuit: multiple companies confirmed
    if verified_ticker == "MULTIPLE":
        logger.info("Supervisor decision: UNSUPPORTED (multiple companies confirmed)")
        return {"next_step": "UNSUPPORTED", "final_response": _UNSUPPORTED_MESSAGE}

    if verified_ticker:
        prompt = f"""
        You are a financial research assistant routing user questions about SEC filings.
        Analyze the question: "{question}"

        The question is about an S&P 500 company (ticker: {verified_ticker}).
        Decide how to handle it:

        1. SEARCH  — the question asks about the company's financials, risks, business strategy,
                     or other SEC filing content. Go ahead and search.
                     Example: "What are Airbnb's main risk factors?"

        2. CLARIFY — the question mentions the company but is too vague to search meaningfully.
                     Example: "Tell me about Airbnb" (no specific financial topic)

        3. REJECT  — the question mentions the company but has nothing to do with its financials
                     or SEC filings.
                     Example: "Where is the closest Airbnb apartment?"
        """
        response = _single_company_llm.invoke([SystemMessage(content=prompt)])
    else:
        prompt = f"""
        You are a financial research assistant routing user questions about SEC filings.
        Analyze the question: "{question}"

        No specific S&P 500 company was confirmed in the question. Choose between:

        1. REJECT      — the question has absolutely nothing to do with finance, business, or
                         SEC filings. Use this ONLY for completely off-topic questions.
                         Example: "What is the weather today?", "Who won the football match?"

        2. UNSUPPORTED — the question is finance-related but refers to an entity that is clearly
                         NOT an S&P 500 company: a private company, university, government body,
                         non-US company, or a sector/industry as a whole.
                         Examples: "Harvard University risks", "how do tech companies discuss AI?"

        3. CLARIFY     — the question is finance-related AND mentions a company name, but that
                         name was not matched to an S&P 500 listing. This includes popular brand
                         names that differ from the legal company name (e.g. "Google" instead of
                         "Alphabet", "Facebook" instead of "Meta Platforms"). Ask the user to
                         clarify or confirm the correct company name.
                         Also use this when the question is too vague with no company mentioned.
                         Examples: "What is Google's net income?", "What are the main risks?"

        4. SEARCH      — the question is about a specific company that may have been missed
                         by automated detection (e.g. a minor typo). Try to search.
                         Example: "What are Alphabbet's risks?" (typo for Alphabet)
        """
        response = _no_company_llm.invoke([SystemMessage(content=prompt)])

    decision = response.next_step  # type: ignore[union-attr]
    logger.info("Supervisor decision: %s", decision)

    if decision == "UNSUPPORTED":
        return {"next_step": "UNSUPPORTED", "final_response": _UNSUPPORTED_MESSAGE}

    if verified_ticker and decision == "SEARCH":
        return {"next_step": decision, "ticker": verified_ticker}

    return {"next_step": decision}
