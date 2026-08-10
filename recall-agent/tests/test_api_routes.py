from fastapi.testclient import TestClient


def test_core_data_can_be_created_and_listed(client: TestClient) -> None:
    business_response = client.post(
        "/businesses",
        json={"name": "Fresh Auto Spa", "industry": "Auto detailing"},
    )
    assert business_response.status_code == 201
    business = business_response.json()
    assert business["name"] == "Fresh Auto Spa"

    customer_response = client.post(
        "/customers",
        json={
            "business_id": business["id"],
            "full_name": "Sarah Ahmed",
            "email": "sarah@example.com",
            "preferred_channel": "email",
            "is_opted_in": True,
        },
    )
    assert customer_response.status_code == 201
    customer = customer_response.json()
    assert customer["full_name"] == "Sarah Ahmed"

    service_type_response = client.post(
        "/service-types",
        json={
            "business_id": business["id"],
            "name": "Interior Detailing",
            "recommended_interval_days": 60,
        },
    )
    assert service_type_response.status_code == 201
    service_type = service_type_response.json()
    assert service_type["recommended_interval_days"] == 60

    service_record_response = client.post(
        "/service-records",
        json={
            "customer_id": customer["id"],
            "service_type_id": service_type["id"],
            "service_date": "2026-08-09",
            "notes": "First test service record",
        },
    )
    assert service_record_response.status_code == 201
    service_record = service_record_response.json()
    assert service_record["service_date"] == "2026-08-09"

    assert client.get("/businesses").json() == [business]
    assert client.get("/customers").json() == [customer]
    assert client.get("/service-types").json() == [service_type]
    assert client.get("/service-records").json() == [service_record]
    assert client.get("/reminders").json() == []
    assert client.get("/agent-logs").json() == []


def test_customer_requires_existing_business(client: TestClient) -> None:
    response = client.post(
        "/customers",
        json={"business_id": 999, "full_name": "Missing Business Customer"},
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Business not found"


def test_service_record_requires_same_business(client: TestClient) -> None:
    first_business = client.post("/businesses", json={"name": "Business One"}).json()
    second_business = client.post("/businesses", json={"name": "Business Two"}).json()
    customer = client.post(
        "/customers",
        json={"business_id": first_business["id"], "full_name": "Sarah Ahmed"},
    ).json()
    service_type = client.post(
        "/service-types",
        json={
            "business_id": second_business["id"],
            "name": "Deep Cleaning",
            "recommended_interval_days": 90,
        },
    ).json()

    response = client.post(
        "/service-records",
        json={
            "customer_id": customer["id"],
            "service_type_id": service_type["id"],
            "service_date": "2026-08-09",
        },
    )

    assert response.status_code == 400
    assert response.json()["detail"] == (
        "Customer and service type must belong to the same business"
    )
