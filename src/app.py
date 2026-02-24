import traceback

import streamlit as st

from graph.blueprint import app
from utils.config import settings
from utils.logging import logger


def check_password():
    """Returns `True` if the user had the correct password."""

    def password_entered():
        """Checks whether a password entered by the user is correct."""
        if (
            st.session_state["password"]
            == settings.DEEP_FINANCIAL_RESEARCH_PASSWORD.get_secret_value()
        ):
            st.session_state["password_correct"] = True
            del st.session_state["password"]  # don't store password
        else:
            st.session_state["password_correct"] = False

    if "password_correct" not in st.session_state:
        # First run, show input for password.
        st.text_input("Password", type="password", on_change=password_entered, key="password")
        return False
    elif not st.session_state["password_correct"]:
        # Password not correct, show input + error.
        st.text_input("Password", type="password", on_change=password_entered, key="password")
        st.error("😕 Password incorrect")
        return False
    else:
        # Password correct.
        return True


# --- PAGE CONFIG ---
st.set_page_config(page_title="Deep Financial Research", page_icon="📈")

if not check_password():
    st.stop()  # Do not continue if check_password is not True.

st.title("📈 Deep Financial Research Assistant")
st.markdown("Search across SEC filings for **NVDA** and **AAPL**.")

# --- DISCLAIMER ---
st.warning(
    """
⚠️ **DISCLAIMER: This is a simple Proof of Concept (POC) with very limited abilities.**

- This tool can **only** analyze SEC filings for NVIDIA (NVDA) and Apple (AAPL)
- It should **NOT** be used to obtain actual financial information for investment decisions
- This is for demonstration purposes only
- Always consult professional financial advisors and official sources for investment guidance
"""
)

# --- SESSION STATE ---
# This keeps the chat history alive in the browser
if "messages" not in st.session_state:
    st.session_state.messages = []

# Display previous messages
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# --- SEARCH BAR (Chat Input) ---
if prompt := st.chat_input("Ask about company financials or risks..."):
    # 1. Add user message to UI
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # 2. Run the LangGraph
    with st.spinner("Analyzing filings..."):
        try:
            # Initial state for the graph
            inputs = {"question": prompt}

            # Run the graph (this triggers supervisor -> search -> reply)
            result = app.invoke(inputs)

            # Extract the final answer
            answer = result.get("final_response", "I'm sorry, I couldn't process that.")

            # 3. Add assistant response to UI
            with st.chat_message("assistant"):
                st.markdown(answer)
            st.session_state.messages.append({"role": "assistant", "content": answer})

        except Exception as e:
            st.error(f"An error occurred: {e}")
            logger.error(f"App Error: {e}")
            logger.error(traceback.format_exc())
