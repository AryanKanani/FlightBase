from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session, joinedload

from app.db.session import get_db
from app.models import Flight
from app.schemas.flight import FlightRead


router = APIRouter(prefix="/flights", tags=["Flights"])


@router.get("/", response_model=list[FlightRead])
def list_flights(db: Session = Depends(get_db)) -> list[FlightRead]:
    flights = (
        db.query(Flight)
        .options(
            joinedload(Flight.airline),
            joinedload(Flight.origin_airport),
            joinedload(Flight.destination_airport),
        )
        .order_by(Flight.flight_id)
        .all()
    )

    return [
        FlightRead(
            flight_id=flight.flight_id,
            flight_number=flight.flight_number,
            airline_name=flight.airline.name,
            origin_airport_name=flight.origin_airport.name,
            origin_airport_code=flight.origin_airport.iata_code,
            destination_airport_name=flight.destination_airport.name,
            destination_airport_code=flight.destination_airport.iata_code,
        )
        for flight in flights
    ]


@router.get("/{flight_id}", response_model=FlightRead)
def get_flight(flight_id: int, db: Session = Depends(get_db)) -> FlightRead:
    flight = (
        db.query(Flight)
        .options(
            joinedload(Flight.airline),
            joinedload(Flight.origin_airport),
            joinedload(Flight.destination_airport),
        )
        .filter(Flight.flight_id == flight_id)
        .first()
    )

    if not flight:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Flight not found.",
        )

    return FlightRead(
        flight_id=flight.flight_id,
        flight_number=flight.flight_number,
        airline_name=flight.airline.name,
        origin_airport_name=flight.origin_airport.name,
        origin_airport_code=flight.origin_airport.iata_code,
        destination_airport_name=flight.destination_airport.name,
        destination_airport_code=flight.destination_airport.iata_code,
    )
