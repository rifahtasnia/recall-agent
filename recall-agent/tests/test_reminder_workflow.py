from datetime import date, timedelta

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.db.models import AgentLog, Reminder


def create_base_records(
    client: TestClient,
    *,
    interval_days: int = 30,
    days_ago: int = 31,
    is_opted_in: bool = True,
    preferred_channel: str = "email",
    email: str | None = "customer@example.com",
    phone: str | None = "+14165550100",
) -> dict:
    business = client.post("/businesses", json={"name": "Workflow Test Co"}).json()
    customer = client.post(
        "/customers",
        json={
            "business_id": business["id"],
            "full_name": "Sarah Ahmed",
            "email": email,
            "phone": phone,
            "preferred_channel": preferred_channel,
            "is_opted_in": is_opted_in,
        },
    ).json()
    service_type = client.post(
        "/service-types",
        json={
            "business_id": business["id"],
            "name": "Interior Detailing",
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


def test_reminder_run_creates_due_reminder(
    client: TestClient, db_session: Session
) -> None:
    records = create_base_records(client, interval_days=30, days_ago=45)

    response = client.post("/reminder-runs")

    assert response.status_code == 201
    payload = response.json()
    assert payload["processed"] == 1
    assert payload["created"] == 1
    assert payload["skipped"] == 0
    assert payload["details"][0]["decision"] == "created"

    reminder = db_session.query(Reminder).one()
    assert reminder.customer_id == records["customer"]["id"]
    assert reminder.service_record_id == records["service_record"]["id"]
    assert reminder.status == "pending"
    assert "Interior Detailing" in reminder.message

    agent_log = db_session.query(AgentLog).one()
    assert agent_log.decision == "created"
    assert agent_log.reminder_id == reminder.id


def test_reminder_run_skips_service_that_is_not_due(client: TestClient) -> None:
    create_base_records(client, interval_days=30, days_ago=10)

    payload = client.post("/reminder-runs").json()

    assert payload["processed"] == 1
    assert payload["created"] == 0
    assert payload["skipped"] == 1
    assert payload["details"][0]["decision"] == "skipped"
    assert "not due yet" in payload["details"][0]["reason"]


def test_reminder_run_skips_opted_out_customer(client: TestClient) -> None:
    create_base_records(client, is_opted_in=False)

    payload = client.post("/reminder-runs").json()

    assert payload["created"] == 0
    assert payload["skipped"] == 1
    assert "opted out" in payload["details"][0]["reason"]


def test_reminder_run_skips_missing_preferred_contact(client: TestClient) -> None:
    create_base_records(client, preferred_channel="sms", phone=None)

    payload = client.post("/reminder-runs").json()

    assert payload["created"] == 0
    assert payload["skipped"] == 1
    assert "does not have a phone number" in payload["details"][0]["reason"]


def test_reminder_run_prevents_duplicate_reminders(client: TestClient) -> None:
    create_base_records(client)

    first_run = client.post("/reminder-runs").json()
    second_run = client.post("/reminder-runs").json()

    assert first_run["created"] == 1
    assert second_run["created"] == 0
    assert second_run["skipped"] == 1
    assert "already exists" in second_run["details"][0]["reason"]
