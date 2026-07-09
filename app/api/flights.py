from datetime import datetime, time, timedelta

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session, joinedload

from app.db.session import get_db
from app.models import Airport, Fare, Flight, Schedule, Seat, Ticket
from app.schemas.flight import FlightRead, FlightSearchRead


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


@router.get("/search", response_model=list[FlightSearchRead])
def search_flights(
    source: str,
    destination: str,
    travel_date: str,
    seat_class: str = "Economy",
    db: Session = Depends(get_db),
) -> list[FlightSearchRead]:
    try:
        parsed_date = datetime.strptime(travel_date, "%Y-%m-%d").date()
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="travel_date must use YYYY-MM-DD format.",
        ) from exc

    source_code = source.strip().upper()
    destination_code = destination.strip().upper()
    seat_class_name = seat_class.strip()
    departure_start = datetime.combine(parsed_date, time.min)
    departure_end = departure_start + timedelta(days=1)

    schedules = (
        db.query(Schedule)
        .options(
            joinedload(Schedule.flight).joinedload(Flight.airline),
            joinedload(Schedule.flight).joinedload(Flight.origin_airport),
            joinedload(Schedule.flight).joinedload(Flight.destination_airport),
        )
        .filter(
            Schedule.flight.has(
                Flight.origin_airport.has(Airport.iata_code == source_code)
            ),
            Schedule.flight.has(
                Flight.destination_airport.has(Airport.iata_code == destination_code)
            ),
            Schedule.departure_time >= departure_start,
            Schedule.departure_time < departure_end,
        )
        .order_by(Schedule.departure_time)
        .all()
    )

    results = []
    for schedule in schedules:
        fare = (
            db.query(Fare)
            .options(joinedload(Fare.seat_class))
            .filter(Fare.flight_id == schedule.flight_id)
            .filter(Fare.seat_class.has(class_name=seat_class_name))
            .first()
        )
        if fare is None:
            continue

        total_seats = (
            db.query(Seat)
            .filter(
                Seat.aircraft_id == schedule.aircraft_id,
                Seat.class_id == fare.class_id,
            )
            .count()
        )
        booked_seats = (
            db.query(Ticket)
            .filter(Ticket.schedule_id == schedule.schedule_id)
            .join(Ticket.seat)
            .filter(Seat.class_id == fare.class_id)
            .count()
        )

        results.append(
            FlightSearchRead(
                schedule_id=schedule.schedule_id,
                flight_id=schedule.flight_id,
                flight_number=schedule.flight.flight_number,
                airline_name=schedule.flight.airline.name,
                source=schedule.flight.origin_airport.iata_code,
                destination=schedule.flight.destination_airport.iata_code,
                travel_date=schedule.departure_time.date(),
                departure_time=schedule.departure_time.strftime("%H:%M"),
                arrival_time=schedule.arrival_time.strftime("%H:%M"),
                seat_class=fare.seat_class.class_name,
                price=fare.price,
                available_seats=total_seats - booked_seats,
            )
        )

    return results


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
