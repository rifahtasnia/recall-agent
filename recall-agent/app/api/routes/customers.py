from fastapi import APIRouter, HTTPException
from sqlalchemy import select

from app.api.deps import DbSession
from app.db.models import Business, Customer
from app.schemas import CustomerCreate, CustomerRead

router = APIRouter(prefix="/customers", tags=["customers"])


@router.post("", response_model=CustomerRead, status_code=201)
def create_customer(payload: CustomerCreate, db: DbSession) -> Customer:
    business = db.get(Business, payload.business_id)
    if business is None:
        raise HTTPException(status_code=404, detail="Business not found")

    customer = Customer(**payload.model_dump())
    db.add(customer)
    db.commit()
    db.refresh(customer)
    return customer


@router.get("", response_model=list[CustomerRead])
def list_customers(db: DbSession) -> list[Customer]:
    return list(db.scalars(select(Customer).order_by(Customer.id)))
