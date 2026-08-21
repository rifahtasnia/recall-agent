from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field

from app.db.models import AgentLogStatus, ReminderStatus


class BusinessCreate(BaseModel):
    name: str = Field(min_length=1, max_length=150)
    industry: str | None = Field(default=None, max_length=100)


class BusinessRead(BusinessCreate):
    id: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class CustomerCreate(BaseModel):
    business_id: int
    full_name: str = Field(min_length=1, max_length=150)
    email: str | None = Field(default=None, max_length=255)
    phone: str | None = Field(default=None, max_length=40)
    preferred_channel: str = Field(default="email", max_length=20)
    is_opted_in: bool = True


class CustomerRead(CustomerCreate):
    id: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ServiceTypeCreate(BaseModel):
    business_id: int
    name: str = Field(min_length=1, max_length=120)
    description: str | None = None
    recommended_interval_days: int = Field(gt=0)


class ServiceTypeRead(ServiceTypeCreate):
    id: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ServiceRecordCreate(BaseModel):
    customer_id: int
    service_type_id: int
    service_date: date
    notes: str | None = None


class ServiceRecordRead(ServiceRecordCreate):
    id: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ReminderRead(BaseModel):
    id: int
    customer_id: int
    service_type_id: int
    service_record_id: int
    scheduled_for: date
    channel: str
    message: str
    status: ReminderStatus
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class AgentLogRead(BaseModel):
    id: int
    customer_id: int
    reminder_id: int | None
    agent_name: str
    decision: AgentLogStatus
    reason: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class CustomerFrequencyInsightRead(BaseModel):
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

    model_config = ConfigDict(from_attributes=True)


class ReminderRunDecisionRead(BaseModel):
    service_record_id: int
    customer_id: int
    service_type_id: int
    decision: AgentLogStatus
    reason: str
    reminder_id: int | None = None

    model_config = ConfigDict(from_attributes=True)


class ReminderRunRead(BaseModel):
    processed: int
    created: int
    skipped: int
    details: list[ReminderRunDecisionRead]

    model_config = ConfigDict(from_attributes=True)
