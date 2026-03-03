"""Password authentication component."""

import bcrypt

import streamlit as st

from utils.config import settings


def check_password() -> bool:
    """Returns `True` if the user had the correct password."""

    def password_entered():
        """Checks whether a password entered by the user is correct."""
        if bcrypt.checkpw(
            st.session_state["password"].encode(),
            settings.DEEP_FINANCIAL_RESEARCH_PASSWORD.get_secret_value().encode(),
        ):
            st.session_state["password_correct"] = True
            del st.session_state["password"]  # don't store password
        else:
            st.session_state["password_correct"] = False

    if "password_correct" not in st.session_state:
        st.text_input("Password", type="password", on_change=password_entered, key="password")
        return False
    elif not st.session_state["password_correct"]:
        st.text_input("Password", type="password", on_change=password_entered, key="password")
        st.error("Password incorrect")
        return False
    else:
        return True
