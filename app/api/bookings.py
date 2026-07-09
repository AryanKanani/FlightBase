from datetime import date, datetime, time, timedelta

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session, joinedload

from app.db.session import get_db
from app.models import Airport, Booking, Fare, Flight, Passenger, Payment, Schedule, Seat, Ticket
from app.schemas.booking import BookingCreate, BookingDetailRead, BookingRead, TicketBookingCreate


router = APIRouter(prefix="/bookings", tags=["Bookings"])


def _booking_to_detail(booking: Booking) -> BookingDetailRead:
    ticket = booking.tickets[0] if booking.tickets else None
    payment = booking.payments[0] if booking.payments else None

    if ticket is None or payment is None:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Booking is missing ticket or payment details.",
        )

    schedule = ticket.schedule
    flight = schedule.flight

    return BookingDetailRead(
        booking_id=booking.booking_id,
        booking_date=booking.booking_date,
        status=booking.status,
        passenger_id=booking.passenger_id,
        passenger_name=booking.passenger.name,
        email=booking.passenger.email,
        phone=booking.passenger.phone,
        passport_no=booking.passenger.passport_no,
        ticket_id=ticket.ticket_id,
        flight_number=flight.flight_number,
        source=flight.origin_airport.iata_code,
        destination=flight.destination_airport.iata_code,
        travel_date=schedule.departure_time.date(),
        departure_time=schedule.departure_time.strftime("%H:%M"),
        arrival_time=schedule.arrival_time.strftime("%H:%M"),
        seat_number=ticket.seat.seat_number,
        seat_class=ticket.fare.seat_class.class_name,
        ticket_price=ticket.price,
        payment_id=payment.payment_id,
        payment_method=payment.method,
        payment_date=payment.payment_date,
    )


def _booking_detail_options():
    return (
        joinedload(Booking.passenger),
        joinedload(Booking.payments),
        joinedload(Booking.tickets).joinedload(Ticket.seat),
        joinedload(Booking.tickets).joinedload(Ticket.fare).joinedload(Fare.seat_class),
        joinedload(Booking.tickets)
        .joinedload(Ticket.schedule)
        .joinedload(Schedule.flight)
        .joinedload(Flight.origin_airport),
        joinedload(Booking.tickets)
        .joinedload(Ticket.schedule)
        .joinedload(Schedule.flight)
        .joinedload(Flight.destination_airport),
    )


@router.get("/", response_model=list[BookingRead])
def list_bookings(db: Session = Depends(get_db)) -> list[BookingRead]:
    bookings = (
        db.query(Booking)
        .options(joinedload(Booking.passenger))
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


@router.get("/flight/{flight_id}", response_model=list[BookingDetailRead], include_in_schema=False)
def list_bookings_for_flight(
    flight_id: int,
    db: Session = Depends(get_db),
) -> list[BookingDetailRead]:
    flight = db.query(Flight).filter(Flight.flight_id == flight_id).first()
    if not flight:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Flight not found.",
        )

    bookings = (
        db.query(Booking)
        .join(Booking.tickets)
        .join(Ticket.schedule)
        .options(*_booking_detail_options())
        .filter(Schedule.flight_id == flight_id)
        .order_by(Booking.booking_id)
        .all()
    )

    return [_booking_to_detail(booking) for booking in bookings]


@router.get("/flight-number/{flight_number}", response_model=list[BookingDetailRead])
def list_bookings_for_flight_number(
    flight_number: str,
    db: Session = Depends(get_db),
) -> list[BookingDetailRead]:
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

    bookings = (
        db.query(Booking)
        .join(Booking.tickets)
        .join(Ticket.schedule)
        .options(*_booking_detail_options())
        .filter(Schedule.flight_id == flight.flight_id)
        .order_by(Booking.booking_id)
        .all()
    )

    return [_booking_to_detail(booking) for booking in bookings]


@router.get("/passenger/{passenger_id}", response_model=list[BookingDetailRead])
def list_bookings_for_passenger(
    passenger_id: int,
    db: Session = Depends(get_db),
) -> list[BookingDetailRead]:
    passenger = db.query(Passenger).filter(Passenger.passenger_id == passenger_id).first()
    if not passenger:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Passenger not found.",
        )

    bookings = (
        db.query(Booking)
        .options(*_booking_detail_options())
        .filter(Booking.passenger_id == passenger_id)
        .order_by(Booking.booking_id)
        .all()
    )

    return [_booking_to_detail(booking) for booking in bookings]


@router.post("/book-ticket", response_model=BookingDetailRead, status_code=status.HTTP_201_CREATED)
def book_ticket(payload: TicketBookingCreate, db: Session = Depends(get_db)) -> BookingDetailRead:
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
            detail="No scheduled flight found for this route and date.",
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
            detail="No fare found for this seat class.",
        )

    booked_seat_ids = (
        db.query(Ticket.seat_id)
        .filter(Ticket.schedule_id == schedule.schedule_id)
        .subquery()
    )
    seat = (
        db.query(Seat)
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
            detail="No available seat found for this flight and class.",
        )

    passenger = db.query(Passenger).filter(Passenger.email == payload.email).first()
    if passenger and passenger.passport_no != payload.passport_no:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already belongs to a passenger with a different passport number.",
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
                detail="Passport number already belongs to another passenger.",
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
    db.commit()

    booking = (
        db.query(Booking)
        .options(*_booking_detail_options())
        .filter(Booking.booking_id == booking.booking_id)
        .first()
    )
    return _booking_to_detail(booking)


@router.get("/{booking_id}", response_model=BookingDetailRead)
def get_booking(booking_id: int, db: Session = Depends(get_db)) -> BookingDetailRead:
    booking = (
        db.query(Booking)
        .options(*_booking_detail_options())
        .filter(Booking.booking_id == booking_id)
        .first()
    )

    if not booking:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Booking not found.",
        )

    return _booking_to_detail(booking)


@router.put("/{booking_id}/cancel", response_model=BookingDetailRead)
def cancel_booking(booking_id: int, db: Session = Depends(get_db)) -> BookingDetailRead:
    booking = (
        db.query(Booking)
        .options(*_booking_detail_options())
        .filter(Booking.booking_id == booking_id)
        .first()
    )
    if not booking:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Booking not found.",
        )
    if booking.status == "Cancelled":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Booking is already cancelled.",
        )

    booking.status = "Cancelled"
    db.commit()
    db.refresh(booking)
    return _booking_to_detail(booking)


@router.post("/", response_model=BookingRead, status_code=status.HTTP_201_CREATED, include_in_schema=False)
def create_booking(payload: BookingCreate, db: Session = Depends(get_db)) -> BookingRead:
    passenger = db.query(Passenger).filter(Passenger.passenger_id == payload.passenger_id).first()
    if not passenger:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Passenger not found.",
        )

    booking = Booking(
        passenger_id=payload.passenger_id,
        booking_date=date.today(),
        status="Confirmed",
        total_price=payload.total_price,
    )
    db.add(booking)
    db.commit()
    db.refresh(booking)

    return BookingRead(
        booking_id=booking.booking_id,
        passenger_id=booking.passenger_id,
        passenger_name=passenger.name,
        booking_date=booking.booking_date,
        status=booking.status,
        total_price=booking.total_price,
    )
