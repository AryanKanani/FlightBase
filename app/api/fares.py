from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session, joinedload

from app.db.session import get_db
from app.models import Fare
from app.schemas.fare import FareRead


router = APIRouter(prefix="/fares", tags=["Fares"])


@router.get("/", response_model=list[FareRead])
def list_fares(db: Session = Depends(get_db)) -> list[FareRead]:
    fares = (
        db.query(Fare)
        .options(
            joinedload(Fare.flight),
            joinedload(Fare.seat_class),
        )
        .order_by(Fare.fare_id)
        .all()
    )

    return [
        FareRead(
            fare_id=fare.fare_id,
            flight_number=fare.flight.flight_number,
            seat_class=fare.seat_class.class_name,
            price=fare.price,
        )
        for fare in fares
    ]


@router.get("/{fare_id}", response_model=FareRead, include_in_schema=False)
def get_fare(fare_id: int, db: Session = Depends(get_db)) -> FareRead:
    fare = (
        db.query(Fare)
        .options(
            joinedload(Fare.flight),
            joinedload(Fare.seat_class),
        )
        .filter(Fare.fare_id == fare_id)
        .first()
    )

    if not fare:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Fare not found.",
        )

    return FareRead(
        fare_id=fare.fare_id,
        flight_number=fare.flight.flight_number,
        seat_class=fare.seat_class.class_name,
        price=fare.price,
    )
