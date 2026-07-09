from datetime import date

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session, joinedload

from app.db.session import get_db
from app.models import Booking, Passenger
from app.schemas.booking import BookingCreate, BookingRead


router = APIRouter(prefix="/bookings", tags=["Bookings"])


@router.get("/", response_model=list[BookingRead])
def list_bookings(db: Session = Depends(get_db)) -> list[BookingRead]:
    bookings = (
        db.query(Booking)
        .options(joinedload(Booking.passenger))
        .order_by(Booking.booking_id)
        .all()
    )

    return [
        BookingRead(
            booking_id=booking.booking_id,
            passenger_id=booking.passenger_id,
            passenger_name=booking.passenger.name,
            booking_date=booking.booking_date,
            status=booking.status,
            total_price=booking.total_price,
        )
        for booking in bookings
    ]


@router.post("/", response_model=BookingRead, status_code=status.HTTP_201_CREATED)
def create_booking(payload: BookingCreate, db: Session = Depends(get_db)) -> BookingRead:
    passenger = db.query(Passenger).filter(Passenger.passenger_id == payload.passenger_id).first()
    if not passenger:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Passenger not found.",
        )

    booking = Booking(
        passenger_id=payload.passenger_id,
        booking_date=date.today(),
        status="Confirmed",
        total_price=payload.total_price,
    )
    db.add(booking)
    db.commit()
    db.refresh(booking)

    return BookingRead(
        booking_id=booking.booking_id,
        passenger_id=booking.passenger_id,
        passenger_name=passenger.name,
        booking_date=booking.booking_date,
        status=booking.status,
        total_price=booking.total_price,
    )
