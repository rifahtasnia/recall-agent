from dataclasses import dataclass
from datetime import date, timedelta
from enum import StrEnum

from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.core.config import get_settings
from app.db.models import (
    AgentLog,
    AgentLogStatus,
    Reminder,
    ServiceRecord,
)
from app.services.customer_frequency import (
    CustomerFrequencyInsight,
    get_frequency_insight_for_record,
)
from app.services.reminder_workflow import get_latest_service_record_ids

AGENT_NAME = "LLMReminderDecisionAgent"


class LLMReminderDecision(StrEnum):
    send_reminder = "send_reminder"
    skip_reminder = "skip_reminder"
    needs_review = "needs_review"


class LLMReminderDecisionOutput(BaseModel):
    decision: LLMReminderDecision
    reason: str = Field(min_length=1)


@dataclass(frozen=True)
class ReminderDecisionContext:
    service_record_id: int
    customer_id: int
    customer_name: str
    service_type_id: int
    service_name: str
    service_date: date
    run_date: date
    days_since_service: int
    due_date: date
    is_latest_service_record: bool
    customer_is_opted_in: bool
    preferred_channel: str
    has_required_contact: bool
    existing_reminder_id: int | None
    frequency_insight: CustomerFrequencyInsight
    rule_recommendation: LLMReminderDecision
    rule_reason: str


@dataclass(frozen=True)
class LLMReminderRunDecision:
    service_record_id: int
    customer_id: int
    service_type_id: int
    decision: LLMReminderDecision
    reason: str
    source: str
    rule_recommendation: LLMReminderDecision
    rule_reason: str


@dataclass(frozen=True)
class LLMReminderRunResult:
    processed: int
    send_reminder: int
    skip_reminder: int
    needs_review: int
    details: list[LLMReminderRunDecision]


def run_llm_reminder_decision_agent(
    db: Session, run_date: date | None = None
) -> LLMReminderRunResult:
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
    latest_service_record_ids = get_latest_service_record_ids(service_records)

    decisions: list[LLMReminderRunDecision] = []
    for service_record in service_records:
        context = build_reminder_decision_context(
            db,
            service_record=service_record,
            today=today,
            latest_service_record_ids=latest_service_record_ids,
        )
        decision = decide_with_llm_or_fallback(context)
        log_llm_decision(db, decision)
        decisions.append(decision)

    db.commit()

    return LLMReminderRunResult(
        processed=len(decisions),
        send_reminder=count_decisions(decisions, LLMReminderDecision.send_reminder),
        skip_reminder=count_decisions(decisions, LLMReminderDecision.skip_reminder),
        needs_review=count_decisions(decisions, LLMReminderDecision.needs_review),
        details=decisions,
    )


def build_reminder_decision_context(
    db: Session,
    *,
    service_record: ServiceRecord,
    today: date,
    latest_service_record_ids: set[int],
) -> ReminderDecisionContext:
    customer = service_record.customer
    service_type = service_record.service_type
    frequency_insight = get_frequency_insight_for_record(db, service_record)
    due_date = service_record.service_date + timedelta(
        days=frequency_insight.effective_interval_days
    )
    existing_reminder = db.scalar(
        select(Reminder).where(Reminder.service_record_id == service_record.id)
    )
    has_required_contact = customer_has_required_contact(
        preferred_channel=customer.preferred_channel,
        email=customer.email,
        phone=customer.phone,
    )
    is_latest = service_record.id in latest_service_record_ids
    rule_recommendation, rule_reason = get_rule_recommendation(
        customer_name=customer.full_name,
        service_name=service_type.name,
        due_date=due_date,
        existing_reminder_id=existing_reminder.id if existing_reminder else None,
        has_required_contact=has_required_contact,
        is_latest_service_record=is_latest,
        customer_is_opted_in=customer.is_opted_in,
        today=today,
    )

    return ReminderDecisionContext(
        service_record_id=service_record.id,
        customer_id=customer.id,
        customer_name=customer.full_name,
        service_type_id=service_type.id,
        service_name=service_type.name,
        service_date=service_record.service_date,
        run_date=today,
        days_since_service=(today - service_record.service_date).days,
        due_date=due_date,
        is_latest_service_record=is_latest,
        customer_is_opted_in=customer.is_opted_in,
        preferred_channel=customer.preferred_channel,
        has_required_contact=has_required_contact,
        existing_reminder_id=existing_reminder.id if existing_reminder else None,
        frequency_insight=frequency_insight,
        rule_recommendation=rule_recommendation,
        rule_reason=rule_reason,
    )


def get_rule_recommendation(
    *,
    customer_name: str,
    service_name: str,
    due_date: date,
    existing_reminder_id: int | None,
    has_required_contact: bool,
    is_latest_service_record: bool,
    customer_is_opted_in: bool,
    today: date,
) -> tuple[LLMReminderDecision, str]:
    if not is_latest_service_record:
        return (
            LLMReminderDecision.skip_reminder,
            "A newer service record exists, so this record is history only.",
        )

    if not customer_is_opted_in:
        return (
            LLMReminderDecision.skip_reminder,
            f"{customer_name} has opted out of reminders.",
        )

    if not has_required_contact:
        return (
            LLMReminderDecision.needs_review,
            f"{customer_name} is missing the required contact for their channel.",
        )

    if existing_reminder_id is not None:
        return (
            LLMReminderDecision.skip_reminder,
            f"Reminder {existing_reminder_id} already exists for this service record.",
        )

    if today < due_date:
        return (
            LLMReminderDecision.skip_reminder,
            f"{service_name} is not due yet; next due date is {due_date}.",
        )

    return (
        LLMReminderDecision.send_reminder,
        f"{service_name} is due and the customer can be contacted.",
    )


def decide_with_llm_or_fallback(
    context: ReminderDecisionContext,
) -> LLMReminderRunDecision:
    settings = get_settings()
    if not settings.openai_api_key:
        return build_fallback_decision(context)

    try:
        llm_output = call_langchain_decision_agent(context)
    except Exception as exc:
        return LLMReminderRunDecision(
            service_record_id=context.service_record_id,
            customer_id=context.customer_id,
            service_type_id=context.service_type_id,
            decision=context.rule_recommendation,
            reason=(
                f"LLM decision failed, so the rule recommendation was used. "
                f"Error: {exc}"
            ),
            source="rule_fallback_after_llm_error",
            rule_recommendation=context.rule_recommendation,
            rule_reason=context.rule_reason,
        )

    safe_decision = enforce_safety_boundary(context, llm_output.decision)
    return LLMReminderRunDecision(
        service_record_id=context.service_record_id,
        customer_id=context.customer_id,
        service_type_id=context.service_type_id,
        decision=safe_decision,
        reason=llm_output.reason,
        source="langchain_llm",
        rule_recommendation=context.rule_recommendation,
        rule_reason=context.rule_reason,
    )


def call_langchain_decision_agent(
    context: ReminderDecisionContext,
) -> LLMReminderDecisionOutput:
    from langchain_core.prompts import ChatPromptTemplate
    from langchain_openai import ChatOpenAI

    prompt = ChatPromptTemplate.from_messages(
        [
            (
                "system",
                "You are RecallAgent, a customer retention decision agent for local "
                "service businesses. Use the structured context to decide whether a "
                "reminder should be sent. Do not override opt-out, missing contact, "
                "duplicate reminder, or stale service-record safety rules.",
            ),
            (
                "human",
                "Decision context:\n{context}\n\nReturn a structured decision and a "
                "short business-friendly reason.",
            ),
        ]
    )
    model = ChatOpenAI(model="gpt-4o-mini", temperature=0)
    chain = prompt | model.with_structured_output(LLMReminderDecisionOutput)
    return chain.invoke({"context": build_llm_context_payload(context)})


def build_llm_context_payload(context: ReminderDecisionContext) -> dict:
    return {
        "customer": {
            "id": context.customer_id,
            "name": context.customer_name,
            "is_opted_in": context.customer_is_opted_in,
            "preferred_channel": context.preferred_channel,
            "has_required_contact": context.has_required_contact,
        },
        "service": {
            "service_record_id": context.service_record_id,
            "service_type_id": context.service_type_id,
            "name": context.service_name,
            "service_date": str(context.service_date),
            "days_since_service": context.days_since_service,
            "due_date": str(context.due_date),
            "is_latest_service_record": context.is_latest_service_record,
        },
        "frequency": {
            "source": context.frequency_insight.source,
            "record_count": context.frequency_insight.record_count,
            "default_interval_days": context.frequency_insight.default_interval_days,
            "average_gap_days": context.frequency_insight.average_gap_days,
            "effective_interval_days": (
                context.frequency_insight.effective_interval_days
            ),
            "service_dates": [
                str(service_date)
                for service_date in context.frequency_insight.service_dates
            ],
        },
        "rule_recommendation": {
            "decision": context.rule_recommendation,
            "reason": context.rule_reason,
        },
    }


def build_fallback_decision(
    context: ReminderDecisionContext,
) -> LLMReminderRunDecision:
    return LLMReminderRunDecision(
        service_record_id=context.service_record_id,
        customer_id=context.customer_id,
        service_type_id=context.service_type_id,
        decision=context.rule_recommendation,
        reason=(
            f"{context.rule_reason} No OpenAI API key is configured, so the "
            "deterministic rule recommendation was used."
        ),
        source="rule_fallback_no_api_key",
        rule_recommendation=context.rule_recommendation,
        rule_reason=context.rule_reason,
    )


def enforce_safety_boundary(
    context: ReminderDecisionContext,
    llm_decision: LLMReminderDecision,
) -> LLMReminderDecision:
    if context.rule_recommendation != LLMReminderDecision.send_reminder:
        return context.rule_recommendation

    return llm_decision


def customer_has_required_contact(
    *, preferred_channel: str, email: str | None, phone: str | None
) -> bool:
    if preferred_channel == "email":
        return bool(email)

    if preferred_channel == "sms":
        return bool(phone)

    return False


def log_llm_decision(db: Session, decision: LLMReminderRunDecision) -> None:
    db.add(
        AgentLog(
            customer_id=decision.customer_id,
            reminder_id=None,
            agent_name=AGENT_NAME,
            decision=map_llm_decision_to_log_status(decision.decision),
            reason=(
                f"{decision.decision}: {decision.reason} Source: {decision.source}."
            ),
        )
    )


def map_llm_decision_to_log_status(
    decision: LLMReminderDecision,
) -> AgentLogStatus:
    if decision == LLMReminderDecision.send_reminder:
        return AgentLogStatus.created

    return AgentLogStatus.skipped


def count_decisions(
    decisions: list[LLMReminderRunDecision],
    target_decision: LLMReminderDecision,
) -> int:
    return sum(1 for decision in decisions if decision.decision == target_decision)
