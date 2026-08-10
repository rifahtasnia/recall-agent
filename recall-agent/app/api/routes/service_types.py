from fastapi import APIRouter, HTTPException
from sqlalchemy import select

from app.api.deps import DbSession
from app.db.models import Business, ServiceType
from app.schemas import ServiceTypeCreate, ServiceTypeRead

router = APIRouter(prefix="/service-types", tags=["service types"])


@router.post("", response_model=ServiceTypeRead, status_code=201)
def create_service_type(payload: ServiceTypeCreate, db: DbSession) -> ServiceType:
    business = db.get(Business, payload.business_id)
    if business is None:
        raise HTTPException(status_code=404, detail="Business not found")

    service_type = ServiceType(**payload.model_dump())
    db.add(service_type)
    db.commit()
    db.refresh(service_type)
    return service_type


@router.get("", response_model=list[ServiceTypeRead])
def list_service_types(db: DbSession) -> list[ServiceType]:
    return list(db.scalars(select(ServiceType).order_by(ServiceType.id)))
