from fastapi import APIRouter, HTTPException
from sqlalchemy import select

from app.api.deps import DbSession
from app.db.models import Customer, ServiceRecord, ServiceType
from app.schemas import ServiceRecordCreate, ServiceRecordRead

router = APIRouter(prefix="/service-records", tags=["service records"])


@router.post("", response_model=ServiceRecordRead, status_code=201)
def create_service_record(payload: ServiceRecordCreate, db: DbSession) -> ServiceRecord:
    customer = db.get(Customer, payload.customer_id)
    if customer is None:
        raise HTTPException(status_code=404, detail="Customer not found")

    service_type = db.get(ServiceType, payload.service_type_id)
    if service_type is None:
        raise HTTPException(status_code=404, detail="Service type not found")

    if customer.business_id != service_type.business_id:
        raise HTTPException(
            status_code=400,
            detail="Customer and service type must belong to the same business",
        )

    service_record = ServiceRecord(**payload.model_dump())
    db.add(service_record)
    db.commit()
    db.refresh(service_record)
    return service_record


@router.get("", response_model=list[ServiceRecordRead])
def list_service_records(db: DbSession) -> list[ServiceRecord]:
    return list(db.scalars(select(ServiceRecord).order_by(ServiceRecord.id)))
