from datetime import date, timedelta

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import Business, Customer, ServiceRecord, ServiceType
from app.db.session import SessionLocal

BUSINESS_NAME = "Fresh Auto Spa"


def get_or_create_business(db: Session) -> Business:
    business = db.scalar(select(Business).where(Business.name == BUSINESS_NAME))
    if business is not None:
        return business

    business = Business(name=BUSINESS_NAME, industry="Auto detailing")
    db.add(business)
    db.flush()
    return business


def get_or_create_service_type(
    db: Session,
    business: Business,
    name: str,
    interval_days: int,
    description: str,
) -> ServiceType:
    service_type = db.scalar(
        select(ServiceType).where(
            ServiceType.business_id == business.id,
            ServiceType.name == name,
        )
    )
    if service_type is not None:
        return service_type

    service_type = ServiceType(
        business_id=business.id,
        name=name,
        description=description,
        recommended_interval_days=interval_days,
    )
    db.add(service_type)
    db.flush()
    return service_type


def get_or_create_customer(
    db: Session,
    business: Business,
    full_name: str,
    email: str,
    phone: str,
    preferred_channel: str,
) -> Customer:
    customer = db.scalar(
        select(Customer).where(
            Customer.business_id == business.id,
            Customer.email == email,
        )
    )
    if customer is not None:
        return customer

    customer = Customer(
        business_id=business.id,
        full_name=full_name,
        email=email,
        phone=phone,
        preferred_channel=preferred_channel,
        is_opted_in=True,
    )
    db.add(customer)
    db.flush()
    return customer


def get_or_create_service_record(
    db: Session,
    customer: Customer,
    service_type: ServiceType,
    service_date: date,
    notes: str,
) -> ServiceRecord:
    service_record = db.scalar(
        select(ServiceRecord).where(
            ServiceRecord.customer_id == customer.id,
            ServiceRecord.service_type_id == service_type.id,
            ServiceRecord.service_date == service_date,
        )
    )
    if service_record is not None:
        return service_record

    service_record = ServiceRecord(
        customer_id=customer.id,
        service_type_id=service_type.id,
        service_date=service_date,
        notes=notes,
    )
    db.add(service_record)
    db.flush()
    return service_record


def seed_database() -> None:
    today = date.today()

    with SessionLocal() as db:
        business = get_or_create_business(db)

        basic_wash = get_or_create_service_type(
            db,
            business,
            name="Basic Car Wash",
            interval_days=30,
            description="Exterior wash and quick interior tidy-up.",
        )
        interior_detailing = get_or_create_service_type(
            db,
            business,
            name="Interior Detailing",
            interval_days=60,
            description="Deep interior vacuum, wipe-down, and refresh.",
        )
        full_detailing = get_or_create_service_type(
            db,
            business,
            name="Full Detailing",
            interval_days=90,
            description="Interior and exterior detailing package.",
        )

        sarah = get_or_create_customer(
            db,
            business,
            full_name="Sarah Ahmed",
            email="sarah.ahmed@example.com",
            phone="+14165550100",
            preferred_channel="email",
        )
        daniel = get_or_create_customer(
            db,
            business,
            full_name="Daniel Khan",
            email="daniel.khan@example.com",
            phone="+14165550101",
            preferred_channel="sms",
        )
        mina = get_or_create_customer(
            db,
            business,
            full_name="Mina Chowdhury",
            email="mina.chowdhury@example.com",
            phone="+14165550102",
            preferred_channel="email",
        )

        get_or_create_service_record(
            db,
            sarah,
            interior_detailing,
            today - timedelta(days=63),
            "Interior detailing completed. Customer prefers weekday reminders.",
        )
        get_or_create_service_record(
            db,
            daniel,
            basic_wash,
            today - timedelta(days=28),
            "Basic wash completed. Customer usually books by SMS.",
        )
        get_or_create_service_record(
            db,
            mina,
            full_detailing,
            today - timedelta(days=96),
            "Full detailing completed before a long road trip.",
        )

        db.commit()


if __name__ == "__main__":
    seed_database()
    print("Seed data loaded.")
