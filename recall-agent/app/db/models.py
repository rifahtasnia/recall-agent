from datetime import date, datetime
from enum import StrEnum

from sqlalchemy import Boolean, Date, DateTime, Enum, ForeignKey, Integer, String, Text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from sqlalchemy.sql import func


class Base(DeclarativeBase):
    pass


class ReminderStatus(StrEnum):
    pending = "pending"
    scheduled = "scheduled"
    sent = "sent"
    skipped = "skipped"
    failed = "failed"


class AgentLogStatus(StrEnum):
    created = "created"
    skipped = "skipped"
    failed = "failed"


class Business(Base):
    __tablename__ = "businesses"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(150), nullable=False)
    industry: Mapped[str | None] = mapped_column(String(100))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    customers: Mapped[list["Customer"]] = relationship(
        back_populates="business", cascade="all, delete-orphan"
    )
    service_types: Mapped[list["ServiceType"]] = relationship(
        back_populates="business", cascade="all, delete-orphan"
    )


class Customer(Base):
    __tablename__ = "customers"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    business_id: Mapped[int] = mapped_column(
        ForeignKey("businesses.id"), nullable=False
    )
    full_name: Mapped[str] = mapped_column(String(150), nullable=False)
    email: Mapped[str | None] = mapped_column(String(255))
    phone: Mapped[str | None] = mapped_column(String(40))
    preferred_channel: Mapped[str] = mapped_column(String(20), default="email")
    is_opted_in: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    business: Mapped["Business"] = relationship(back_populates="customers")
    service_records: Mapped[list["ServiceRecord"]] = relationship(
        back_populates="customer", cascade="all, delete-orphan"
    )
    reminders: Mapped[list["Reminder"]] = relationship(
        back_populates="customer", cascade="all, delete-orphan"
    )


class ServiceType(Base):
    __tablename__ = "service_types"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    business_id: Mapped[int] = mapped_column(
        ForeignKey("businesses.id"), nullable=False
    )
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    recommended_interval_days: Mapped[int] = mapped_column(Integer, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    business: Mapped["Business"] = relationship(back_populates="service_types")
    service_records: Mapped[list["ServiceRecord"]] = relationship(
        back_populates="service_type"
    )
    reminders: Mapped[list["Reminder"]] = relationship(back_populates="service_type")


class ServiceRecord(Base):
    __tablename__ = "service_records"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    customer_id: Mapped[int] = mapped_column(ForeignKey("customers.id"), nullable=False)
    service_type_id: Mapped[int] = mapped_column(
        ForeignKey("service_types.id"), nullable=False
    )
    service_date: Mapped[date] = mapped_column(Date, nullable=False)
    notes: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    customer: Mapped["Customer"] = relationship(back_populates="service_records")
    service_type: Mapped["ServiceType"] = relationship(back_populates="service_records")
    reminders: Mapped[list["Reminder"]] = relationship(back_populates="service_record")


class Reminder(Base):
    __tablename__ = "reminders"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    customer_id: Mapped[int] = mapped_column(ForeignKey("customers.id"), nullable=False)
    service_type_id: Mapped[int] = mapped_column(
        ForeignKey("service_types.id"), nullable=False
    )
    service_record_id: Mapped[int] = mapped_column(
        ForeignKey("service_records.id"), nullable=False
    )
    scheduled_for: Mapped[date] = mapped_column(Date, nullable=False)
    channel: Mapped[str] = mapped_column(String(20), nullable=False)
    message: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[ReminderStatus] = mapped_column(
        Enum(ReminderStatus, name="reminder_status"),
        default=ReminderStatus.pending,
        nullable=False,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    customer: Mapped["Customer"] = relationship(back_populates="reminders")
    service_type: Mapped["ServiceType"] = relationship(back_populates="reminders")
    service_record: Mapped["ServiceRecord"] = relationship(back_populates="reminders")
    agent_logs: Mapped[list["AgentLog"]] = relationship(
        back_populates="reminder", cascade="all, delete-orphan"
    )


class AgentLog(Base):
    __tablename__ = "agent_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    customer_id: Mapped[int] = mapped_column(ForeignKey("customers.id"), nullable=False)
    reminder_id: Mapped[int | None] = mapped_column(ForeignKey("reminders.id"))
    agent_name: Mapped[str] = mapped_column(String(100), nullable=False)
    decision: Mapped[AgentLogStatus] = mapped_column(
        Enum(AgentLogStatus, name="agent_log_status"), nullable=False
    )
    reason: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    customer: Mapped["Customer"] = relationship()
    reminder: Mapped["Reminder"] = relationship(back_populates="agent_logs")
