from datetime import date, timedelta
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import Business, Customer, ServiceRecord, ServiceType
from app.db.session import SessionLocal

SeedData = dict[str, Any]


DEMO_DATA: list[SeedData] = [
    {
        "business": {
            "name": "Fresh Auto Spa",
            "industry": "Auto detailing",
        },
        "service_types": [
            {
                "key": "basic_wash",
                "name": "Basic Car Wash",
                "interval_days": 30,
                "description": "Exterior wash and quick interior tidy-up.",
            },
            {
                "key": "interior_detailing",
                "name": "Interior Detailing",
                "interval_days": 60,
                "description": "Deep interior vacuum, wipe-down, and refresh.",
            },
            {
                "key": "full_detailing",
                "name": "Full Detailing",
                "interval_days": 90,
                "description": "Interior and exterior detailing package.",
            },
            {
                "key": "ceramic_checkup",
                "name": "Ceramic Coating Checkup",
                "interval_days": 180,
                "description": "Inspection and maintenance for ceramic coating.",
            },
        ],
        "customers": [
            {
                "key": "sarah",
                "full_name": "Sarah Ahmed",
                "email": "sarah.ahmed@example.com",
                "phone": "+14165550100",
                "preferred_channel": "email",
            },
            {
                "key": "daniel",
                "full_name": "Daniel Khan",
                "email": "daniel.khan@example.com",
                "phone": "+14165550101",
                "preferred_channel": "sms",
            },
            {
                "key": "mina",
                "full_name": "Mina Chowdhury",
                "email": "mina.chowdhury@example.com",
                "phone": "+14165550102",
                "preferred_channel": "email",
                "is_opted_in": False,
            },
            {
                "key": "omar",
                "full_name": "Omar Rahman",
                "email": "omar.rahman@example.com",
                "phone": "+14165550103",
                "preferred_channel": "sms",
            },
            {
                "key": "james",
                "full_name": "James Carter",
                "email": None,
                "phone": "+14165550104",
                "preferred_channel": "sms",
            },
            {
                "key": "priya",
                "full_name": "Priya Shah",
                "email": "priya.shah@example.com",
                "phone": None,
                "preferred_channel": "email",
            },
        ],
        "service_records": [
            {
                "customer_key": "sarah",
                "service_type_key": "interior_detailing",
                "days_ago": 142,
                "notes": (
                    "Earlier interior detailing visit. Shows repeat service history."
                ),
            },
            {
                "customer_key": "sarah",
                "service_type_key": "interior_detailing",
                "days_ago": 63,
                "notes": (
                    "Interior detailing completed. Customer prefers weekday reminders."
                ),
            },
            {
                "customer_key": "daniel",
                "service_type_key": "basic_wash",
                "days_ago": 28,
                "notes": "Basic wash completed. Customer usually books by SMS.",
            },
            {
                "customer_key": "daniel",
                "service_type_key": "basic_wash",
                "days_ago": 58,
                "notes": "Previous wash for repeat-frequency comparison.",
            },
            {
                "customer_key": "mina",
                "service_type_key": "full_detailing",
                "days_ago": 96,
                "notes": "Opted-out customer. Should be skipped even if overdue.",
            },
            {
                "customer_key": "omar",
                "service_type_key": "ceramic_checkup",
                "days_ago": 155,
                "notes": "Ceramic coating checkup completed. Not due yet.",
            },
            {
                "customer_key": "james",
                "service_type_key": "basic_wash",
                "days_ago": 31,
                "notes": "SMS-only customer with no email address. Due by SMS.",
            },
            {
                "customer_key": "priya",
                "service_type_key": "full_detailing",
                "days_ago": 4,
                "notes": "Very recent service. Should not receive a reminder.",
            },
            {
                "customer_key": "sarah",
                "service_type_key": "basic_wash",
                "days_ago": 18,
                "notes": "Recent wash after interior detailing.",
            },
        ],
    },
    {
        "business": {
            "name": "Sparkle Home Cleaning",
            "industry": "Residential cleaning",
        },
        "service_types": [
            {
                "key": "standard_cleaning",
                "name": "Standard Home Cleaning",
                "interval_days": 14,
                "description": "Recurring kitchen, bathroom, and floor cleaning.",
            },
            {
                "key": "deep_cleaning",
                "name": "Home Deep Cleaning",
                "interval_days": 90,
                "description": "Detailed seasonal cleaning for the full home.",
            },
            {
                "key": "move_out",
                "name": "Move-Out Cleaning",
                "interval_days": 180,
                "description": "One-time cleaning for move-out preparation.",
            },
            {
                "key": "carpet_cleaning",
                "name": "Carpet Cleaning",
                "interval_days": 180,
                "description": "Steam cleaning for carpets and rugs.",
            },
        ],
        "customers": [
            {
                "key": "lina",
                "full_name": "Lina Patel",
                "email": "lina.patel@example.com",
                "phone": "+14165550200",
                "preferred_channel": "email",
            },
            {
                "key": "marcus",
                "full_name": "Marcus Lee",
                "email": "marcus.lee@example.com",
                "phone": "+14165550201",
                "preferred_channel": "sms",
            },
            {
                "key": "ayesha",
                "full_name": "Ayesha Noor",
                "email": "ayesha.noor@example.com",
                "phone": "+14165550202",
                "preferred_channel": "email",
            },
            {
                "key": "julia",
                "full_name": "Julia Martins",
                "email": "julia.martins@example.com",
                "phone": "+14165550203",
                "preferred_channel": "email",
                "is_opted_in": False,
            },
            {
                "key": "ben",
                "full_name": "Ben Thompson",
                "email": "ben.thompson@example.com",
                "phone": "+14165550204",
                "preferred_channel": "sms",
            },
        ],
        "service_records": [
            {
                "customer_key": "lina",
                "service_type_key": "standard_cleaning",
                "days_ago": 44,
                "notes": "Older recurring cleaning visit.",
            },
            {
                "customer_key": "lina",
                "service_type_key": "standard_cleaning",
                "days_ago": 30,
                "notes": "Repeat cleaning visit. Helps detect recurring cadence.",
            },
            {
                "customer_key": "lina",
                "service_type_key": "standard_cleaning",
                "days_ago": 16,
                "notes": "Biweekly cleaning customer. Due for standard follow-up.",
            },
            {
                "customer_key": "marcus",
                "service_type_key": "deep_cleaning",
                "days_ago": 102,
                "notes": "Deep cleaning completed after renovation work.",
            },
            {
                "customer_key": "ayesha",
                "service_type_key": "carpet_cleaning",
                "days_ago": 175,
                "notes": "Carpet cleaning completed before Eid gathering.",
            },
            {
                "customer_key": "julia",
                "service_type_key": "move_out",
                "days_ago": 45,
                "notes": "Opted-out customer with a one-time service.",
            },
            {
                "customer_key": "lina",
                "service_type_key": "deep_cleaning",
                "days_ago": 88,
                "notes": "Seasonal deep cleaning almost due.",
            },
            {
                "customer_key": "ben",
                "service_type_key": "standard_cleaning",
                "days_ago": 7,
                "notes": "Recent recurring cleaning. Should not be reminded yet.",
            },
            {
                "customer_key": "ben",
                "service_type_key": "carpet_cleaning",
                "days_ago": 210,
                "notes": "Overdue carpet cleaning with SMS preferred.",
            },
        ],
    },
    {
        "business": {
            "name": "GreenWay Lawn Care",
            "industry": "Lawn care",
        },
        "service_types": [
            {
                "key": "lawn_mowing",
                "name": "Lawn Mowing",
                "interval_days": 14,
                "description": "Recurring mowing and edge trimming.",
            },
            {
                "key": "fertilization",
                "name": "Fertilization Treatment",
                "interval_days": 45,
                "description": "Seasonal fertilization treatment for lawns.",
            },
            {
                "key": "fall_cleanup",
                "name": "Fall Cleanup",
                "interval_days": 365,
                "description": "Leaf removal and end-of-season yard cleanup.",
            },
        ],
        "customers": [
            {
                "key": "nora",
                "full_name": "Nora Wilson",
                "email": "nora.wilson@example.com",
                "phone": "+14165550300",
                "preferred_channel": "email",
            },
            {
                "key": "ethan",
                "full_name": "Ethan Brown",
                "email": "ethan.brown@example.com",
                "phone": "+14165550301",
                "preferred_channel": "sms",
            },
            {
                "key": "fatima",
                "full_name": "Fatima Hassan",
                "email": "fatima.hassan@example.com",
                "phone": "+14165550302",
                "preferred_channel": "email",
            },
            {
                "key": "liam",
                "full_name": "Liam Chen",
                "email": None,
                "phone": None,
                "preferred_channel": "email",
                "is_opted_in": False,
            },
        ],
        "service_records": [
            {
                "customer_key": "nora",
                "service_type_key": "lawn_mowing",
                "days_ago": 43,
                "notes": "Older mowing visit in recurring lawn-care pattern.",
            },
            {
                "customer_key": "nora",
                "service_type_key": "lawn_mowing",
                "days_ago": 29,
                "notes": "Second recurring mowing visit.",
            },
            {
                "customer_key": "nora",
                "service_type_key": "lawn_mowing",
                "days_ago": 15,
                "notes": "Routine mowing completed. Customer is on a two-week cycle.",
            },
            {
                "customer_key": "ethan",
                "service_type_key": "fertilization",
                "days_ago": 52,
                "notes": "Fertilization treatment completed. Follow-up likely due.",
            },
            {
                "customer_key": "fatima",
                "service_type_key": "fall_cleanup",
                "days_ago": 290,
                "notes": "Fall cleanup completed last season. Not due yet.",
            },
            {
                "customer_key": "liam",
                "service_type_key": "fertilization",
                "days_ago": 70,
                "notes": "No usable contact details and opted out. Must be skipped.",
            },
        ],
    },
]


def get_or_create_business(db: Session, name: str, industry: str) -> Business:
    business = db.scalar(select(Business).where(Business.name == name))
    if business is not None:
        return business

    business = Business(name=name, industry=industry)
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
    email: str | None,
    phone: str | None,
    preferred_channel: str,
    is_opted_in: bool,
) -> Customer:
    if email is not None:
        customer = db.scalar(
            select(Customer).where(
                Customer.business_id == business.id,
                Customer.email == email,
            )
        )
    else:
        customer = db.scalar(
            select(Customer).where(
                Customer.business_id == business.id,
                Customer.full_name == full_name,
            )
        )

    if customer is not None:
        customer.full_name = full_name
        customer.email = email
        customer.phone = phone
        customer.preferred_channel = preferred_channel
        customer.is_opted_in = is_opted_in
        return customer

    customer = Customer(
        business_id=business.id,
        full_name=full_name,
        email=email,
        phone=phone,
        preferred_channel=preferred_channel,
        is_opted_in=is_opted_in,
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


def seed_business(db: Session, business_data: SeedData, today: date) -> None:
    business = get_or_create_business(
        db,
        name=business_data["business"]["name"],
        industry=business_data["business"]["industry"],
    )

    service_types = {
        service_type_data["key"]: get_or_create_service_type(
            db,
            business,
            name=service_type_data["name"],
            interval_days=service_type_data["interval_days"],
            description=service_type_data["description"],
        )
        for service_type_data in business_data["service_types"]
    }

    customers = {
        customer_data["key"]: get_or_create_customer(
            db,
            business,
            full_name=customer_data["full_name"],
            email=customer_data["email"],
            phone=customer_data["phone"],
            preferred_channel=customer_data["preferred_channel"],
            is_opted_in=customer_data.get("is_opted_in", True),
        )
        for customer_data in business_data["customers"]
    }

    for record_data in business_data["service_records"]:
        get_or_create_service_record(
            db,
            customer=customers[record_data["customer_key"]],
            service_type=service_types[record_data["service_type_key"]],
            service_date=today - timedelta(days=record_data["days_ago"]),
            notes=record_data["notes"],
        )


def seed_database() -> None:
    today = date.today()

    with SessionLocal() as db:
        for business_data in DEMO_DATA:
            seed_business(db, business_data, today)

        db.commit()


if __name__ == "__main__":
    seed_database()
    print("Seed data loaded.")
