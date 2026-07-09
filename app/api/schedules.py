from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session, joinedload

from app.db.session import get_db
from app.models import Schedule
from app.schemas.schedule import ScheduleRead


router = APIRouter(prefix="/schedules", tags=["Schedules"])


@router.get("/", response_model=list[ScheduleRead])
def list_schedules(db: Session = Depends(get_db)) -> list[ScheduleRead]:
    schedules = (
        db.query(Schedule)
        .options(
            joinedload(Schedule.flight),
            joinedload(Schedule.aircraft),
        )
        .order_by(Schedule.schedule_id)
        .all()
    )

    return [
        ScheduleRead(
            schedule_id=schedule.schedule_id,
            flight_number=schedule.flight.flight_number,
            aircraft_model=schedule.aircraft.model,
            departure_time=schedule.departure_time,
            arrival_time=schedule.arrival_time,
            status=schedule.status,
        )
        for schedule in schedules
    ]


@router.get("/{schedule_id}", response_model=ScheduleRead)
def get_schedule(schedule_id: int, db: Session = Depends(get_db)) -> ScheduleRead:
    schedule = (
        db.query(Schedule)
        .options(
            joinedload(Schedule.flight),
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

    return ScheduleRead(
        schedule_id=schedule.schedule_id,
        flight_number=schedule.flight.flight_number,
        aircraft_model=schedule.aircraft.model,
        departure_time=schedule.departure_time,
        arrival_time=schedule.arrival_time,
        status=schedule.status,
    )
