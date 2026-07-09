from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session, joinedload

from app.db.session import get_db
from app.models import Flight, Schedule
from app.schemas.schedule import ScheduleRead


router = APIRouter(prefix="/schedules", tags=["Schedules"])


def _schedule_to_read(schedule: Schedule) -> ScheduleRead:
    return ScheduleRead(
        schedule_id=schedule.schedule_id,
        flight_number=schedule.flight.flight_number,
        source=schedule.flight.origin_airport.iata_code,
        source_city=schedule.flight.origin_airport.city,
        destination=schedule.flight.destination_airport.iata_code,
        destination_city=schedule.flight.destination_airport.city,
        aircraft_model=schedule.aircraft.model,
        departure_time=schedule.departure_time,
        arrival_time=schedule.arrival_time,
        status=schedule.status,
    )


@router.get("/", response_model=list[ScheduleRead])
def list_schedules(db: Session = Depends(get_db)) -> list[ScheduleRead]:
    schedules = (
        db.query(Schedule)
        .options(
            joinedload(Schedule.flight).joinedload(Flight.origin_airport),
            joinedload(Schedule.flight).joinedload(Flight.destination_airport),
            joinedload(Schedule.aircraft),
        )
        .order_by(Schedule.schedule_id)
        .all()
    )

    return [_schedule_to_read(schedule) for schedule in schedules]


@router.get("/flight-number/{flight_number}", response_model=list[ScheduleRead])
def list_schedules_for_flight_number(
    flight_number: str,
    db: Session = Depends(get_db),
) -> list[ScheduleRead]:
    flight = (
        db.query(Flight)
        .filter(Flight.flight_number == flight_number.strip().upper())
        .first()
    )
    if not flight:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Flight not found.",
        )

    schedules = (
        db.query(Schedule)
        .options(
            joinedload(Schedule.flight).joinedload(Flight.origin_airport),
            joinedload(Schedule.flight).joinedload(Flight.destination_airport),
            joinedload(Schedule.aircraft),
        )
        .filter(Schedule.flight_id == flight.flight_id)
        .order_by(Schedule.departure_time)
        .all()
    )

    return [_schedule_to_read(schedule) for schedule in schedules]


@router.get("/{schedule_id}", response_model=ScheduleRead, include_in_schema=False)
def get_schedule(schedule_id: int, db: Session = Depends(get_db)) -> ScheduleRead:
    schedule = (
        db.query(Schedule)
        .options(
            joinedload(Schedule.flight).joinedload(Flight.origin_airport),
            joinedload(Schedule.flight).joinedload(Flight.destination_airport),
            joinedload(Schedule.aircraft),
        )
        .filter(Schedule.schedule_id == schedule_id)
        .first()
    )

    if not schedule:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Schedule not found.",
        )

    return _schedule_to_read(schedule)
