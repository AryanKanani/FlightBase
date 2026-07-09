from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models import Passenger
from app.schemas.passenger import PassengerCreate, PassengerRead


router = APIRouter(prefix="/passengers", tags=["Passengers"])


@router.get("/", response_model=list[PassengerRead])
def list_passengers(db: Session = Depends(get_db)) -> list[Passenger]:
    return db.query(Passenger).order_by(Passenger.passenger_id).all()


@router.post("/", response_model=PassengerRead, status_code=status.HTTP_201_CREATED)
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
