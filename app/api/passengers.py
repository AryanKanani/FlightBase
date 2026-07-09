from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session, joinedload

from app.db.session import get_db
from app.models import Booking, Passenger
from app.schemas.booking import BookingRead
from app.schemas.passenger import PassengerCreate, PassengerRead


router = APIRouter(prefix="/passengers", tags=["Passengers"])


@router.get("/", response_model=list[PassengerRead])
def list_passengers(db: Session = Depends(get_db)) -> list[Passenger]:
    return db.query(Passenger).order_by(Passenger.passenger_id).all()


@router.get("/{passenger_id}", response_model=PassengerRead)
def get_passenger(passenger_id: int, db: Session = Depends(get_db)) -> Passenger:
    passenger = (
        db.query(Passenger)
        .filter(Passenger.passenger_id == passenger_id)
        .first()
    )
    if not passenger:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Passenger not found.",
        )

    return passenger


@router.get("/{passenger_id}/bookings", response_model=list[BookingRead])
def list_passenger_bookings(
    passenger_id: int,
    db: Session = Depends(get_db),
) -> list[BookingRead]:
    passenger = (
        db.query(Passenger)
        .filter(Passenger.passenger_id == passenger_id)
        .first()
    )
    if not passenger:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Passenger not found.",
        )

    bookings = (
        db.query(Booking)
        .options(joinedload(Booking.passenger))
        .filter(Booking.passenger_id == passenger_id)
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


@router.post("/", response_model=PassengerRead, status_code=status.HTTP_201_CREATED, include_in_schema=False)
def create_passenger(payload: PassengerCreate, db: Session = Depends(get_db)) -> Passenger:
    existing_email = db.query(Passenger).filter(Passenger.email == payload.email).first()
    if existing_email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Passenger with this email already exists.",
        )

    existing_passport = db.query(Passenger).filter(Passenger.passport_no == payload.passport_no).first()
    if existing_passport:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Passenger with this passport number already exists.",
        )

    passenger = Passenger(
        name=payload.name,
        email=payload.email,
        phone=payload.phone,
        passport_no=payload.passport_no,
    )
    db.add(passenger)
    db.commit()
    db.refresh(passenger)
    return passenger
