from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models import Airport
from app.schemas.airport import AirportCreate, AirportRead


router = APIRouter(prefix="/airports", tags=["Airports"])


@router.get("/", response_model=list[AirportRead])
def list_airports(db: Session = Depends(get_db)) -> list[Airport]:
    return db.query(Airport).order_by(Airport.airport_id).all()


@router.post("/", response_model=AirportRead, status_code=status.HTTP_201_CREATED)
def create_airport(payload: AirportCreate, db: Session = Depends(get_db)) -> Airport:
    existing_airport = db.query(Airport).filter(Airport.iata_code == payload.iata_code).first()
    if existing_airport:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Airport with this IATA code already exists.",
        )

    airport = Airport(
        name=payload.name,
        city=payload.city,
        country=payload.country,
        iata_code=payload.iata_code,
    )
    db.add(airport)
    db.commit()
    db.refresh(airport)
    return airport
