"""Header and disclaimer component."""

import streamlit as st


def render_header():
    """Render the page title and disclaimer."""
    st.title("Deep Financial Research Assistant")
    st.markdown("Search across SEC filings for **NVDA** and **AAPL**.")

    st.warning(
        """
**DISCLAIMER: This is a simple Proof of Concept (POC) with very limited abilities.**

- This tool can **only** analyze SEC filings for NVIDIA (NVDA) and Apple (AAPL)
- It should **NOT** be used to obtain actual financial information for investment decisions
- This is for demonstration purposes only
- Always consult professional financial advisors and official sources for investment guidance
"""
    )
