import os

import requests
import streamlit as st

API_URL = os.getenv("API_URL", "http://localhost:8000")

st.set_page_config(page_title="RecallAgent", page_icon="RA", layout="wide")

st.title("RecallAgent")
st.caption("Customer retention agent dashboard")


def fetch_json(path: str) -> list[dict] | dict | None:
    try:
        response = requests.get(f"{API_URL}{path}", timeout=5)
        response.raise_for_status()
    except requests.RequestException as exc:
        st.error(f"Could not load {path}: {exc}")
        return None

    return response.json()


health = fetch_json("/health")
db_health = fetch_json("/health/db")

status_columns = st.columns(2)

with status_columns[0]:
    st.subheader("API Status")
    if health:
        st.success(f"{health['app']} API is running")
        st.caption(f"Environment: {health['environment']}")

with status_columns[1]:
    st.subheader("Database Status")
    if db_health:
        st.success("Database connected")

businesses = fetch_json("/businesses") or []
customers = fetch_json("/customers") or []
service_types = fetch_json("/service-types") or []
service_records = fetch_json("/service-records") or []
reminders = fetch_json("/reminders") or []
agent_logs = fetch_json("/agent-logs") or []
frequency_insights = fetch_json("/customer-frequency-insights") or []

metric_columns = st.columns(7)
metric_columns[0].metric("Businesses", len(businesses))
metric_columns[1].metric("Customers", len(customers))
metric_columns[2].metric("Service Types", len(service_types))
metric_columns[3].metric("Service Records", len(service_records))
metric_columns[4].metric("Reminders", len(reminders))
metric_columns[5].metric("Agent Logs", len(agent_logs))
metric_columns[6].metric("Frequency Insights", len(frequency_insights))

tabs = st.tabs(
    [
        "Businesses",
        "Customers",
        "Service Types",
        "Service Records",
        "Reminders",
        "Agent Logs",
        "Frequency Insights",
    ]
)


def show_table(rows: list[dict], empty_message: str) -> None:
    if rows:
        st.dataframe(rows, use_container_width=True, hide_index=True)
    else:
        st.info(empty_message)


with tabs[0]:
    show_table(businesses, "No businesses available yet.")

with tabs[1]:
    show_table(customers, "No customers available yet.")

with tabs[2]:
    show_table(service_types, "No service types available yet.")

with tabs[3]:
    show_table(service_records, "No service records available yet.")

with tabs[4]:
    show_table(reminders, "No reminders have been created yet.")

with tabs[5]:
    show_table(agent_logs, "No agent decisions have been logged yet.")

with tabs[6]:
    show_table(frequency_insights, "No customer frequency insights available yet.")

with st.expander("Run LLM-assisted decision agent"):
    st.caption("Creates agent decision logs. Reminder records are not sent from here.")
    if st.button("Run decision agent"):
        try:
            response = requests.post(f"{API_URL}/llm-reminder-runs", timeout=10)
            response.raise_for_status()
        except requests.RequestException as exc:
            st.error(f"Could not run LLM decision agent: {exc}")
        else:
            st.success("LLM-assisted decision run completed")
            st.json(response.json())

with st.expander("Raw API health payloads"):
    st.json({"api": health, "database": db_health})
