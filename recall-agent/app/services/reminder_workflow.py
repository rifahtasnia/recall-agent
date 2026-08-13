from dataclasses import dataclass
from datetime import date, timedelta

from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.db.models import (
    AgentLog,
    AgentLogStatus,
    Reminder,
    ReminderStatus,
    ServiceRecord,
)

AGENT_NAME = "RuleBasedReminderWorkflow"


@dataclass(frozen=True)
class ReminderRunDecision:
    service_record_id: int
    customer_id: int
    service_type_id: int
    decision: AgentLogStatus
    reason: str
    reminder_id: int | None = None


@dataclass(frozen=True)
class ReminderRunResult:
    processed: int
    created: int
    skipped: int
    details: list[ReminderRunDecision]


def run_rule_based_reminder_workflow(
    db: Session, run_date: date | None = None
) -> ReminderRunResult:
    today = run_date or date.today()
    service_records = list(
        db.scalars(
            select(ServiceRecord)
            .options(
                joinedload(ServiceRecord.customer),
                joinedload(ServiceRecord.service_type),
            )
            .order_by(ServiceRecord.id)
        )
    )

    details: list[ReminderRunDecision] = []

    for service_record in service_records:
        decision = evaluate_service_record(db, service_record, today)
        details.append(decision)

    db.commit()

    created = sum(1 for detail in details if detail.decision == AgentLogStatus.created)
    skipped = sum(1 for detail in details if detail.decision == AgentLogStatus.skipped)

    return ReminderRunResult(
        processed=len(details),
        created=created,
        skipped=skipped,
        details=details,
    )


def evaluate_service_record(
    db: Session, service_record: ServiceRecord, today: date
) -> ReminderRunDecision:
    customer = service_record.customer
    service_type = service_record.service_type
    due_date = service_record.service_date + timedelta(
        days=service_type.recommended_interval_days
    )

    if today < due_date:
        days_until_due = (due_date - today).days
        return log_decision(
            db,
            service_record=service_record,
            decision=AgentLogStatus.skipped,
            reason=(
                f"{service_type.name} is not due yet. "
                f"Recommended interval is {service_type.recommended_interval_days} "
                f"days; due in {days_until_due} day(s) on {due_date}."
            ),
        )

    if not customer.is_opted_in:
        return log_decision(
            db,
            service_record=service_record,
            decision=AgentLogStatus.skipped,
            reason=f"{customer.full_name} has opted out of reminders.",
        )

    missing_contact_reason = get_missing_contact_reason(
        preferred_channel=customer.preferred_channel,
        email=customer.email,
        phone=customer.phone,
    )
    if missing_contact_reason is not None:
        return log_decision(
            db,
            service_record=service_record,
            decision=AgentLogStatus.skipped,
            reason=missing_contact_reason,
        )

    existing_reminder = db.scalar(
        select(Reminder).where(Reminder.service_record_id == service_record.id)
    )
    if existing_reminder is not None:
        return log_decision(
            db,
            service_record=service_record,
            decision=AgentLogStatus.skipped,
            reason=(f"Reminder already exists for service record {service_record.id}."),
            reminder_id=existing_reminder.id,
        )

    days_since_service = (today - service_record.service_date).days
    reminder = Reminder(
        customer_id=customer.id,
        service_type_id=service_type.id,
        service_record_id=service_record.id,
        scheduled_for=today,
        channel=customer.preferred_channel,
        message=create_message(customer.full_name, service_type.name),
        status=ReminderStatus.pending,
    )
    db.add(reminder)
    db.flush()

    return log_decision(
        db,
        service_record=service_record,
        decision=AgentLogStatus.created,
        reason=(
            f"{customer.full_name} is {days_since_service} days past "
            f"{service_type.name}. Recommended interval is "
            f"{service_type.recommended_interval_days} days."
        ),
        reminder_id=reminder.id,
    )


def get_missing_contact_reason(
    preferred_channel: str, email: str | None, phone: str | None
) -> str | None:
    if preferred_channel == "email" and not email:
        return "Customer prefers email but does not have an email address."

    if preferred_channel == "sms" and not phone:
        return "Customer prefers SMS but does not have a phone number."

    if preferred_channel not in {"email", "sms"}:
        return f"Unsupported preferred channel: {preferred_channel}."

    return None


def create_message(customer_name: str, service_name: str) -> str:
    first_name = customer_name.split()[0]
    return (
        f"Hi {first_name}, it may be time for your next {service_name}. "
        "Would you like to book another appointment?"
    )


def log_decision(
    db: Session,
    service_record: ServiceRecord,
    decision: AgentLogStatus,
    reason: str,
    reminder_id: int | None = None,
) -> ReminderRunDecision:
    agent_log = AgentLog(
        customer_id=service_record.customer_id,
        reminder_id=reminder_id,
        agent_name=AGENT_NAME,
        decision=decision,
        reason=reason,
    )
    db.add(agent_log)

    return ReminderRunDecision(
        service_record_id=service_record.id,
        customer_id=service_record.customer_id,
        service_type_id=service_record.service_type_id,
        decision=decision,
        reason=reason,
        reminder_id=reminder_id,
    )
