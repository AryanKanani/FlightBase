from datetime import date

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session, joinedload

from app.db.session import get_db
from app.models import Booking, Fare, Passenger, Payment, Schedule, Seat, Ticket
from app.schemas.reservation import ReservationCreate, ReservationRead


router = APIRouter(prefix="/reservations", tags=["Reservations"])


@router.get("/", response_model=list[ReservationRead])
def list_reservations(db: Session = Depends(get_db)) -> list[ReservationRead]:
    tickets = (
        db.query(Ticket)
        .options(
            joinedload(Ticket.booking).joinedload(Booking.passenger),
            joinedload(Ticket.booking).joinedload(Booking.payments),
            joinedload(Ticket.schedule).joinedload(Schedule.flight),
            joinedload(Ticket.seat),
            joinedload(Ticket.fare).joinedload(Fare.seat_class),
        )
        .order_by(Ticket.ticket_id)
        .all()
    )

    reservations = []
    for ticket in tickets:
        payment = ticket.booking.payments[0] if ticket.booking.payments else None
        if payment is None:
            continue

        reservations.append(
            ReservationRead(
                booking_id=ticket.booking_id,
                ticket_id=ticket.ticket_id,
                payment_id=payment.payment_id,
                passenger_id=ticket.booking.passenger_id,
                passenger_name=ticket.booking.passenger.name,
                schedule_id=ticket.schedule_id,
                flight_number=ticket.schedule.flight.flight_number,
                seat_id=ticket.seat_id,
                seat_number=ticket.seat.seat_number,
                fare_id=ticket.fare_id,
                seat_class=ticket.fare.seat_class.class_name,
                total_price=ticket.booking.total_price,
                payment_method=payment.method,
                booking_date=ticket.booking.booking_date,
                issue_date=ticket.issue_date,
                payment_date=payment.payment_date,
            )
        )

    return reservations


@router.post("/", response_model=ReservationRead, status_code=status.HTTP_201_CREATED)
def create_reservation(
    payload: ReservationCreate,
    db: Session = Depends(get_db),
) -> ReservationRead:
    passenger = (
        db.query(Passenger)
        .filter(Passenger.passenger_id == payload.passenger_id)
        .first()
    )
    if not passenger:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Passenger not found.",
        )

    schedule = (
        db.query(Schedule)
        .options(joinedload(Schedule.flight), joinedload(Schedule.aircraft))
        .filter(Schedule.schedule_id == payload.schedule_id)
        .first()
    )
    if not schedule:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Schedule not found.",
        )

    seat = (
        db.query(Seat)
        .options(joinedload(Seat.seat_class))
        .filter(Seat.seat_id == payload.seat_id)
        .first()
    )
    if not seat:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Seat not found.",
        )

    fare = (
        db.query(Fare)
        .options(joinedload(Fare.seat_class))
        .filter(Fare.fare_id == payload.fare_id)
        .first()
    )
    if not fare:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Fare not found.",
        )

    if seat.aircraft_id != schedule.aircraft_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Seat does not belong to the aircraft used in this schedule.",
        )

    if fare.flight_id != schedule.flight_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Fare does not belong to the flight used in this schedule.",
        )

    if seat.class_id != fare.class_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Seat class does not match fare class.",
        )

    existing_ticket = (
        db.query(Ticket)
        .filter(
            Ticket.schedule_id == payload.schedule_id,
            Ticket.seat_id == payload.seat_id,
        )
        .first()
    )
    if existing_ticket:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="This seat is already assigned for the selected schedule.",
        )

    try:
        today = date.today()
        booking = Booking(
            passenger_id=payload.passenger_id,
            booking_date=today,
            status="Confirmed",
            total_price=fare.price,
        )
        db.add(booking)
        db.flush()

        payment = Payment(
            booking_id=booking.booking_id,
            amount=fare.price,
            method=payload.payment_method,
            payment_date=today,
        )
        db.add(payment)
        db.flush()

        ticket = Ticket(
            booking_id=booking.booking_id,
            schedule_id=payload.schedule_id,
            seat_id=payload.seat_id,
            fare_id=payload.fare_id,
            sequence_number=payload.sequence_number,
            layover_minutes=payload.layover_minutes,
            price=fare.price,
            issue_date=today,
        )
        db.add(ticket)
        db.flush()

        db.commit()
        db.refresh(booking)
        db.refresh(payment)
        db.refresh(ticket)
    except SQLAlchemyError as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Could not create reservation.",
        ) from exc

    return ReservationRead(
        booking_id=booking.booking_id,
        ticket_id=ticket.ticket_id,
        payment_id=payment.payment_id,
        passenger_id=passenger.passenger_id,
        passenger_name=passenger.name,
        schedule_id=schedule.schedule_id,
        flight_number=schedule.flight.flight_number,
        seat_id=seat.seat_id,
        seat_number=seat.seat_number,
        fare_id=fare.fare_id,
        seat_class=fare.seat_class.class_name,
        total_price=booking.total_price,
        payment_method=payment.method,
        booking_date=booking.booking_date,
        issue_date=ticket.issue_date,
        payment_date=payment.payment_date,
    )
