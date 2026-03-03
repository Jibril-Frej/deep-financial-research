"""Rate limiting service."""

import time
from collections import deque

import streamlit as st


def check_rate_limit() -> tuple[bool, str]:
    """
    Returns (is_allowed, error_message).
    Limits: 1 msg/sec and 10 msgs/min.
    """
    now = time.time()

    if "msg_timestamps" not in st.session_state:
        st.session_state.msg_timestamps = deque()

    timestamps = st.session_state.msg_timestamps

    # Drop timestamps older than 60 seconds
    while timestamps and timestamps[0] < now - 60:
        timestamps.popleft()

    # Check per-minute limit (10 messages)
    if len(timestamps) >= 10:
        wait = int(60 - (now - timestamps[0])) + 1
        return False, f"Rate limit reached: max 10 messages per minute. Please wait {wait}s."

    # Check per-second limit (1 message)
    if timestamps and timestamps[-1] >= now - 1:
        return False, "Please wait at least 1 second between messages."

    timestamps.append(now)
    return True, ""
