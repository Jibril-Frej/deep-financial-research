"""Chat interface component."""

import traceback
from typing import cast

import streamlit as st
from langchain_core.messages import BaseMessageChunk

from graph.blueprint import app
from graph.state import GraphState
from services.rate_limit import check_rate_limit
from utils.logging import logger

STATUS_MESSAGES = {
    "supervisor": "🤔 Analyzing your question...",
    "extractor": "🏢 Identifying company and filing section...",
    "search": "🔍 Searching SEC filings for relevant data...",
    "reply": "✍️ Generating detailed response...",
    "clarify": "💡 Processing clarification...",
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


def _run_graph(prompt: str, reply_placeholder) -> str | None:
    """Execute the LangGraph pipeline, streaming reply tokens into reply_placeholder.

    Args:
        prompt: The user's question.
        reply_placeholder: A Streamlit empty() element in the assistant chat bubble
            where reply tokens are streamed as they arrive.

    Returns:
        The final (cleaned) response string, or None on error.
    """
    streamed_reply = ""
    final_result = None

    with st.status("🤔 Analyzing your question...", expanded=False) as status:
        try:
            inputs = cast(GraphState, {"question": prompt})

            for event_type, data in app.stream(inputs, stream_mode=["debug", "messages"]):
                if event_type == "debug":
                    event = cast(dict, data)
                    if event["type"] == "task":
                        node_name = event["payload"]["name"]
                        if node_name in STATUS_MESSAGES:
                            status.update(label=STATUS_MESSAGES[node_name], state="running")

                    elif event["type"] == "task_result":
                        result = dict(event["payload"].get("result", []))
                        if "final_response" in result:
                            final_result = result

                elif event_type == "messages":
                    chunk, metadata = cast(tuple[BaseMessageChunk, dict], data)
                    if (
                        metadata.get("langgraph_node") == "reply"
                        and isinstance(chunk.content, str)
                        and chunk.content
                    ):
                        streamed_reply += chunk.content
                        reply_placeholder.markdown(streamed_reply + "▌")

            status.update(label="✅ Analysis complete", state="complete")

        except Exception as e:
            status.update(label="Error occurred", state="error")
            st.error(f"An error occurred: {e}")
            logger.error("App Error: %s", e)
            logger.error(traceback.format_exc())
            final_result = None

        finally:
            st.session_state.is_processing = False

    if final_result:
        return final_result.get("final_response", "I'm sorry, I couldn't process that.")
    return streamed_reply or None


def _process_pending_prompt():
    """Process a queued prompt after rerun."""
    if not st.session_state.pending_prompt:
        return

    prompt = st.session_state.pending_prompt
    st.session_state.pending_prompt = None

    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        reply_placeholder = st.empty()

    answer = _run_graph(prompt, reply_placeholder)

    if answer:
        reply_placeholder.markdown(answer)
        st.session_state.messages.append({"role": "assistant", "content": answer})

    st.rerun()


def render_chat():
    """Render the full chat interface."""
    _init_session_state()
    _display_chat_history()
    _handle_input()
    _process_pending_prompt()
