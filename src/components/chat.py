"""Chat interface component."""

import traceback

import streamlit as st

from graph.blueprint import app
from services.rate_limit import check_rate_limit
from utils.logging import logger

STATUS_MESSAGES = {
    "supervisor": "Analyzing your question...",
    "search": "Searching SEC filings for relevant data...",
    "reply": "Generating detailed response...",
    "clarify": "Processing clarification...",
}


def _init_session_state():
    """Initialize session state variables for the chat."""
    if "messages" not in st.session_state:
        st.session_state.messages = []
    if "is_processing" not in st.session_state:
        st.session_state.is_processing = False
    if "pending_prompt" not in st.session_state:
        st.session_state.pending_prompt = None


def _display_chat_history():
    """Render all previous messages."""
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])


def _handle_input():
    """Handle new user input from the chat box."""
    if prompt := st.chat_input(
        "Ask about company financials or risks...", disabled=st.session_state.is_processing
    ):
        allowed, rate_limit_msg = check_rate_limit()
        if not allowed:
            st.warning(rate_limit_msg)
            st.stop()

        st.session_state.is_processing = True
        st.session_state.pending_prompt = prompt
        st.rerun()


def _run_graph(prompt: str) -> str | None:
    """Execute the LangGraph pipeline and return the final response."""
    executed_steps = []

    with st.status("Analyzing your question...", expanded=False) as status:
        try:
            inputs = {"question": prompt}
            final_result = None
            executed_steps.append("Started analysis")

            for chunk in app.stream(inputs):
                for node_name, output in chunk.items():
                    if node_name in STATUS_MESSAGES:
                        status.update(label=STATUS_MESSAGES[node_name], state="running")
                        executed_steps.append(f"Executed: {node_name}")

                    if "final_response" in output:
                        final_result = output

            if final_result is None:
                status.update(label="Completing analysis...", state="running")
                final_result = app.invoke(inputs)
                executed_steps.append("Completed fallback processing")

            status.update(label="Analysis complete", state="complete")
            executed_steps.append("Analysis finished successfully")

            st.write("**Execution Steps:**")
            for step in executed_steps:
                st.write(f"- {step}")

        except Exception as e:
            status.update(label="Error occurred", state="error")
            st.error(f"An error occurred: {e}")
            logger.error(f"App Error: {e}")
            logger.error(traceback.format_exc())
            final_result = None

        finally:
            st.session_state.is_processing = False

    if final_result:
        return final_result.get("final_response", "I'm sorry, I couldn't process that.")
    return None


def _process_pending_prompt():
    """Process a queued prompt after rerun."""
    if not st.session_state.pending_prompt:
        return

    prompt = st.session_state.pending_prompt
    st.session_state.pending_prompt = None

    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    answer = _run_graph(prompt)

    if answer:
        with st.chat_message("assistant"):
            st.markdown(answer)
        st.session_state.messages.append({"role": "assistant", "content": answer})

    st.rerun()


def render_chat():
    """Render the full chat interface."""
    _init_session_state()
    _display_chat_history()
    _handle_input()
    _process_pending_prompt()
