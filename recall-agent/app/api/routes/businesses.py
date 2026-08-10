from fastapi import APIRouter
from sqlalchemy import select

from app.api.deps import DbSession
from app.db.models import Business
from app.schemas import BusinessCreate, BusinessRead

router = APIRouter(prefix="/businesses", tags=["businesses"])


@router.post("", response_model=BusinessRead, status_code=201)
def create_business(payload: BusinessCreate, db: DbSession) -> Business:
    business = Business(**payload.model_dump())
    db.add(business)
    db.commit()
    db.refresh(business)
    return business


@router.get("", response_model=list[BusinessRead])
def list_businesses(db: DbSession) -> list[Business]:
    return list(db.scalars(select(Business).order_by(Business.id)))
