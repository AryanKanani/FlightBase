from datetime import date, datetime, time, timedelta

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session, joinedload

from app.db.session import get_db
from app.models import Airport, Booking, Fare, Flight, Passenger, Payment, Schedule, Seat, Ticket
from app.schemas.reservation import ReservationCreate, ReservationRead, SimpleReservationCreate


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


@router.post("/book", response_model=ReservationRead, status_code=status.HTTP_201_CREATED)
def book_ticket(
    payload: SimpleReservationCreate,
    db: Session = Depends(get_db),
) -> ReservationRead:
    source_code = payload.source.strip().upper()
    destination_code = payload.destination.strip().upper()
    seat_class_name = payload.seat_class.strip()
    departure_start = datetime.combine(payload.travel_date, time.min)
    departure_end = departure_start + timedelta(days=1)

    schedule = (
        db.query(Schedule)
        .options(joinedload(Schedule.flight), joinedload(Schedule.aircraft))
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
        .first()
    )

    if not schedule:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No scheduled flight found for this route and travel date.",
        )

    fare = (
        db.query(Fare)
        .options(joinedload(Fare.seat_class))
        .filter(Fare.flight_id == schedule.flight_id)
        .filter(Fare.seat_class.has(class_name=seat_class_name))
        .first()
    )
    if not fare:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No fare found for this route and seat class.",
        )

    booked_seat_ids = (
        db.query(Ticket.seat_id)
        .filter(Ticket.schedule_id == schedule.schedule_id)
        .subquery()
    )
    seat = (
        db.query(Seat)
        .options(joinedload(Seat.seat_class))
        .filter(
            Seat.aircraft_id == schedule.aircraft_id,
            Seat.class_id == fare.class_id,
            Seat.seat_id.not_in(booked_seat_ids),
        )
        .order_by(Seat.seat_number)
        .first()
    )
    if not seat:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No available seat found for this schedule and seat class.",
        )

    try:
        passenger = (
            db.query(Passenger)
            .filter(Passenger.email == payload.email)
            .first()
        )
        if passenger is None:
            existing_passport = (
                db.query(Passenger)
                .filter(Passenger.passport_no == payload.passport_no)
                .first()
            )
            if existing_passport:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="A passenger with this passport number already exists.",
                )

            passenger = Passenger(
                name=payload.passenger_name,
                email=payload.email,
                phone=payload.phone,
                passport_no=payload.passport_no,
            )
            db.add(passenger)
            db.flush()

        today = date.today()
        booking = Booking(
            passenger_id=passenger.passenger_id,
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
            schedule_id=schedule.schedule_id,
            seat_id=seat.seat_id,
            fare_id=fare.fare_id,
            sequence_number=1,
            layover_minutes=0,
            price=fare.price,
            issue_date=today,
        )
        db.add(ticket)
        db.flush()

        db.commit()
        db.refresh(passenger)
        db.refresh(booking)
        db.refresh(payment)
        db.refresh(ticket)
    except HTTPException:
        db.rollback()
        raise
    except SQLAlchemyError as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Could not book ticket.",
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
