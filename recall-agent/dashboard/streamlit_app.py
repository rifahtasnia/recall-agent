import os

import requests
import streamlit as st

API_URL = os.getenv("API_URL", "http://localhost:8000")

st.set_page_config(page_title="RecallAgent", page_icon="RA", layout="wide")

st.title("RecallAgent")
st.caption("Customer retention agent dashboard")

st.subheader("API Status")

try:
    response = requests.get(f"{API_URL}/health", timeout=5)
    response.raise_for_status()
except requests.RequestException as exc:
    st.error(f"API unavailable: {exc}")
else:
    payload = response.json()
    st.success(f"{payload['app']} API is running")
    st.json(payload)
