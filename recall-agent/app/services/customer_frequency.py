from dataclasses import dataclass
from datetime import date
from itertools import groupby

from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.db.models import ServiceRecord


@dataclass(frozen=True)
class CustomerFrequencyInsight:
    customer_id: int
    customer_name: str
    service_type_id: int
    service_name: str
    record_count: int
    service_dates: list[date]
    default_interval_days: int
    average_gap_days: int | None
    effective_interval_days: int
    source: str
    reason: str


def get_customer_frequency_insights(db: Session) -> list[CustomerFrequencyInsight]:
    service_records = list(
        db.scalars(
            select(ServiceRecord)
            .options(
                joinedload(ServiceRecord.customer),
                joinedload(ServiceRecord.service_type),
            )
            .order_by(
                ServiceRecord.customer_id,
                ServiceRecord.service_type_id,
                ServiceRecord.service_date,
                ServiceRecord.id,
            )
        )
    )

    insights: list[CustomerFrequencyInsight] = []
    for (_customer_id, _service_type_id), records_group in groupby(
        service_records,
        key=lambda record: (record.customer_id, record.service_type_id),
    ):
        records = list(records_group)
        insights.append(build_frequency_insight(records))

    return insights


def get_frequency_insight_for_record(
    db: Session, service_record: ServiceRecord
) -> CustomerFrequencyInsight:
    records = list(
        db.scalars(
            select(ServiceRecord)
            .options(
                joinedload(ServiceRecord.customer),
                joinedload(ServiceRecord.service_type),
            )
            .where(
                ServiceRecord.customer_id == service_record.customer_id,
                ServiceRecord.service_type_id == service_record.service_type_id,
            )
            .order_by(ServiceRecord.service_date, ServiceRecord.id)
        )
    )
    return build_frequency_insight(records)


def build_frequency_insight(
    service_records: list[ServiceRecord],
) -> CustomerFrequencyInsight:
    if not service_records:
        raise ValueError("At least one service record is required.")

    sorted_records = sorted(
        service_records,
        key=lambda record: (record.service_date, record.id),
    )
    customer = sorted_records[-1].customer
    service_type = sorted_records[-1].service_type
    service_dates = [record.service_date for record in sorted_records]

    if len(service_dates) == 1:
        return CustomerFrequencyInsight(
            customer_id=customer.id,
            customer_name=customer.full_name,
            service_type_id=service_type.id,
            service_name=service_type.name,
            record_count=1,
            service_dates=service_dates,
            default_interval_days=service_type.recommended_interval_days,
            average_gap_days=None,
            effective_interval_days=service_type.recommended_interval_days,
            source="service_default",
            reason=(
                "Only one service record exists, so the service type's default "
                "interval is used."
            ),
        )

    gaps = [
        (current_date - previous_date).days
        for previous_date, current_date in zip(
            service_dates, service_dates[1:], strict=False
        )
    ]
    average_gap_days = round(sum(gaps) / len(gaps))

    return CustomerFrequencyInsight(
        customer_id=customer.id,
        customer_name=customer.full_name,
        service_type_id=service_type.id,
        service_name=service_type.name,
        record_count=len(service_dates),
        service_dates=service_dates,
        default_interval_days=service_type.recommended_interval_days,
        average_gap_days=average_gap_days,
        effective_interval_days=average_gap_days,
        source="customer_history",
        reason=(
            f"{customer.full_name} has {len(service_dates)} {service_type.name} "
            f"records with an average repeat gap of {average_gap_days} days."
        ),
    )
