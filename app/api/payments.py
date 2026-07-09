from datetime import date

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models import Booking, Payment
from app.schemas.payment import PaymentCreate, PaymentRead


router = APIRouter(prefix="/payments", tags=["Payments"])


@router.get("/", response_model=list[PaymentRead])
def list_payments(db: Session = Depends(get_db)) -> list[Payment]:
    return db.query(Payment).order_by(Payment.payment_id).all()


@router.post("/", response_model=PaymentRead, status_code=status.HTTP_201_CREATED)
def create_payment(payload: PaymentCreate, db: Session = Depends(get_db)) -> Payment:
    booking = db.query(Booking).filter(Booking.booking_id == payload.booking_id).first()
    if not booking:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Booking not found.",
        )

    payment = Payment(
        booking_id=payload.booking_id,
        amount=payload.amount,
        method=payload.method,
        payment_date=date.today(),
    )
    db.add(payment)
    db.commit()
    db.refresh(payment)
    return payment
