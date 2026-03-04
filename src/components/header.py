"""Header and disclaimer component."""

import streamlit as st


def render_header():
    """Render the page title and disclaimer."""
    st.title("Deep Financial Research Assistant")
    st.markdown("Search across SEC 10-K filings for any **S&P 500** company.")

    st.warning(
        """
**DISCLAIMER: This is a simple Proof of Concept (POC) with very limited abilities.**

- This tool can only analyze the latest **10-K filings** for **S&P 500 companies**
- It should **NOT** be used to obtain actual financial information for investment decisions
- This is for demonstration purposes only
- Always consult professional financial advisors and official sources for investment guidance
"""
    )
