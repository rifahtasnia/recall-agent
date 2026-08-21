from datetime import date, timedelta

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.db.models import AgentLog


def create_llm_agent_records(
    client: TestClient,
    *,
    interval_days: int = 30,
    days_ago: int = 45,
    email: str | None = "customer@example.com",
    preferred_channel: str = "email",
) -> dict:
    business = client.post("/businesses", json={"name": "LLM Agent Test Co"}).json()
    customer = client.post(
        "/customers",
        json={
            "business_id": business["id"],
            "full_name": "Nadia Islam",
            "email": email,
            "preferred_channel": preferred_channel,
            "is_opted_in": True,
        },
    ).json()
    service_type = client.post(
        "/service-types",
        json={
            "business_id": business["id"],
            "name": "Premium Car Wash",
            "recommended_interval_days": interval_days,
        },
    ).json()
    service_record = client.post(
        "/service-records",
        json={
            "customer_id": customer["id"],
            "service_type_id": service_type["id"],
            "service_date": str(date.today() - timedelta(days=days_ago)),
        },
    ).json()

    return {
        "customer": customer,
        "service_type": service_type,
        "service_record": service_record,
    }


def test_llm_reminder_run_uses_rule_fallback_without_api_key(
    client: TestClient,
    db_session: Session,
) -> None:
    create_llm_agent_records(client, interval_days=30, days_ago=45)

    response = client.post("/llm-reminder-runs")

    assert response.status_code == 201
    payload = response.json()
    assert payload["processed"] == 1
    assert payload["send_reminder"] == 1
    assert payload["skip_reminder"] == 0
    assert payload["needs_review"] == 0
    assert payload["details"][0]["decision"] == "send_reminder"
    assert payload["details"][0]["source"] == "rule_fallback_no_api_key"
    assert payload["details"][0]["rule_recommendation"] == "send_reminder"

    agent_log = db_session.query(AgentLog).one()
    assert agent_log.agent_name == "LLMReminderDecisionAgent"
    assert agent_log.decision == "created"
    assert "rule_fallback_no_api_key" in agent_log.reason


def test_llm_reminder_run_marks_missing_contact_as_needs_review(
    client: TestClient,
) -> None:
    create_llm_agent_records(
        client,
        interval_days=30,
        days_ago=45,
        email=None,
        preferred_channel="email",
    )

    payload = client.post("/llm-reminder-runs").json()

    assert payload["send_reminder"] == 0
    assert payload["skip_reminder"] == 0
    assert payload["needs_review"] == 1
    assert payload["details"][0]["decision"] == "needs_review"
    assert "missing the required contact" in payload["details"][0]["rule_reason"]
