from fastapi import APIRouter
from sqlalchemy import select

from app.api.deps import DbSession
from app.db.models import AgentLog
from app.schemas import AgentLogRead

router = APIRouter(prefix="/agent-logs", tags=["agent logs"])


@router.get("", response_model=list[AgentLogRead])
def list_agent_logs(db: DbSession) -> list[AgentLog]:
    return list(db.scalars(select(AgentLog).order_by(AgentLog.id)))
