from datetime import date, timedelta

from fastapi.testclient import TestClient


def create_customer_service_pair(
    client: TestClient,
    *,
    recommended_interval_days: int = 30,
) -> dict:
    business = client.post("/businesses", json={"name": "Frequency Test Co"}).json()
    customer = client.post(
        "/customers",
        json={
            "business_id": business["id"],
            "full_name": "Maya Rahman",
            "email": "maya@example.com",
        },
    ).json()
    service_type = client.post(
        "/service-types",
        json={
            "business_id": business["id"],
            "name": "Home Deep Cleaning",
            "recommended_interval_days": recommended_interval_days,
        },
    ).json()

    return {
        "customer": customer,
        "service_type": service_type,
    }


def create_service_record(
    client: TestClient,
    *,
    customer_id: int,
    service_type_id: int,
    service_date: date,
) -> dict:
    return client.post(
        "/service-records",
        json={
            "customer_id": customer_id,
            "service_type_id": service_type_id,
            "service_date": str(service_date),
        },
    ).json()


def test_frequency_insight_uses_service_default_for_single_record(
    client: TestClient,
) -> None:
    pair = create_customer_service_pair(client, recommended_interval_days=45)
    create_service_record(
        client,
        customer_id=pair["customer"]["id"],
        service_type_id=pair["service_type"]["id"],
        service_date=date.today() - timedelta(days=10),
    )

    payload = client.get("/customer-frequency-insights").json()

    assert len(payload) == 1
    insight = payload[0]
    assert insight["record_count"] == 1
    assert insight["average_gap_days"] is None
    assert insight["effective_interval_days"] == 45
    assert insight["source"] == "service_default"


def test_frequency_insight_uses_customer_history_for_repeated_service(
    client: TestClient,
) -> None:
    pair = create_customer_service_pair(client, recommended_interval_days=45)
    today = date.today()
    for days_ago in [80, 50, 20]:
        create_service_record(
            client,
            customer_id=pair["customer"]["id"],
            service_type_id=pair["service_type"]["id"],
            service_date=today - timedelta(days=days_ago),
        )

    payload = client.get("/customer-frequency-insights").json()

    assert len(payload) == 1
    insight = payload[0]
    assert insight["record_count"] == 3
    assert insight["average_gap_days"] == 30
    assert insight["effective_interval_days"] == 30
    assert insight["source"] == "customer_history"
