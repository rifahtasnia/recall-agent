from fastapi import APIRouter

from app.api.deps import DbSession
from app.schemas import CustomerFrequencyInsightRead
from app.services.customer_frequency import get_customer_frequency_insights

router = APIRouter(
    prefix="/customer-frequency-insights",
    tags=["customer frequency insights"],
)


@router.get("", response_model=list[CustomerFrequencyInsightRead])
def list_customer_frequency_insights(
    db: DbSession,
) -> list[CustomerFrequencyInsightRead]:
    return get_customer_frequency_insights(db)
