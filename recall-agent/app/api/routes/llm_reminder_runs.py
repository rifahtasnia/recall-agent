from fastapi import APIRouter

from app.api.deps import DbSession
from app.schemas import LLMReminderRunRead
from app.services.llm_reminder_agent import run_llm_reminder_decision_agent

router = APIRouter(prefix="/llm-reminder-runs", tags=["llm reminder runs"])


@router.post("", response_model=LLMReminderRunRead, status_code=201)
def create_llm_reminder_run(db: DbSession) -> LLMReminderRunRead:
    result = run_llm_reminder_decision_agent(db)
    return LLMReminderRunRead.model_validate(result)
