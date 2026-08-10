from fastapi import APIRouter
from sqlalchemy import select

from app.api.deps import DbSession
from app.db.models import Reminder
from app.schemas import ReminderRead

router = APIRouter(prefix="/reminders", tags=["reminders"])


@router.get("", response_model=list[ReminderRead])
def list_reminders(db: DbSession) -> list[Reminder]:
    return list(db.scalars(select(Reminder).order_by(Reminder.id)))
