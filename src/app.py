import streamlit as st

from graph.blueprint import app
from utils.logging import logger

# --- PAGE CONFIG ---
st.set_page_config(page_title="Deep Financial Research", page_icon="📈")
st.title("📈 Deep Financial Research Assistant")
st.markdown("Search across SEC filings for **NVDA** and **AAPL**.")

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
