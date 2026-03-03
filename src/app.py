"""Main Streamlit app for the Deep Financial Research Assistant."""

import streamlit as st

from components.auth import check_password
from components.chat import render_chat
from components.header import render_header

st.set_page_config(page_title="Deep Financial Research", page_icon="📈")

if not check_password():
    st.stop()

render_header()
render_chat()
