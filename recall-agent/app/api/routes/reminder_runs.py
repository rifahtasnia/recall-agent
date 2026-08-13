from fastapi import APIRouter

from app.api.deps import DbSession
from app.schemas import ReminderRunRead
from app.services.reminder_workflow import run_rule_based_reminder_workflow

router = APIRouter(prefix="/reminder-runs", tags=["reminder runs"])


@router.post("", response_model=ReminderRunRead, status_code=201)
def create_reminder_run(db: DbSession) -> ReminderRunRead:
    result = run_rule_based_reminder_workflow(db)
    return ReminderRunRead.model_validate(result)
