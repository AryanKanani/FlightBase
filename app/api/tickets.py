from datetime import date

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session, joinedload

from app.db.session import get_db
from app.models import Booking, Fare, Schedule, Seat, Ticket
from app.schemas.ticket import TicketCreate, TicketRead


router = APIRouter(prefix="/tickets", tags=["Tickets"])


@router.get("/", response_model=list[TicketRead])
def list_tickets(db: Session = Depends(get_db)) -> list[TicketRead]:
    tickets = (
        db.query(Ticket)
        .options(
            joinedload(Ticket.schedule).joinedload(Schedule.flight),
            joinedload(Ticket.seat),
            joinedload(Ticket.fare),
        )
        .order_by(Ticket.ticket_id)
        .all()
    )

    return [
        TicketRead(
            ticket_id=ticket.ticket_id,
            booking_id=ticket.booking_id,
            schedule_id=ticket.schedule_id,
            seat_id=ticket.seat_id,
            fare_id=ticket.fare_id,
            flight_number=ticket.schedule.flight.flight_number,
            seat_number=ticket.seat.seat_number,
            price=ticket.price,
            issue_date=ticket.issue_date,
        )
        for ticket in tickets
    ]


@router.get("/{ticket_id}", response_model=TicketRead)
def get_ticket(ticket_id: int, db: Session = Depends(get_db)) -> TicketRead:
    ticket = (
        db.query(Ticket)
        .options(
            joinedload(Ticket.schedule).joinedload(Schedule.flight),
            joinedload(Ticket.seat),
            joinedload(Ticket.fare),
        )
        .filter(Ticket.ticket_id == ticket_id)
        .first()
    )

    if not ticket:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Ticket not found.",
        )

    return TicketRead(
        ticket_id=ticket.ticket_id,
        booking_id=ticket.booking_id,
        schedule_id=ticket.schedule_id,
        seat_id=ticket.seat_id,
        fare_id=ticket.fare_id,
        flight_number=ticket.schedule.flight.flight_number,
        seat_number=ticket.seat.seat_number,
        price=ticket.price,
        issue_date=ticket.issue_date,
    )


@router.post("/", response_model=TicketRead, status_code=status.HTTP_201_CREATED)
def create_ticket(payload: TicketCreate, db: Session = Depends(get_db)) -> TicketRead:
    booking = db.query(Booking).filter(Booking.booking_id == payload.booking_id).first()
    if not booking:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Booking not found.",
        )

    schedule = (
        db.query(Schedule)
        .options(joinedload(Schedule.flight))
        .filter(Schedule.schedule_id == payload.schedule_id)
        .first()
    )
    if not schedule:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Schedule not found.",
        )

    seat = db.query(Seat).filter(Seat.seat_id == payload.seat_id).first()
    if not seat:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Seat not found.",
        )

    fare = db.query(Fare).filter(Fare.fare_id == payload.fare_id).first()
    if not fare:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Fare not found.",
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

    ticket = Ticket(
        booking_id=payload.booking_id,
        schedule_id=payload.schedule_id,
        seat_id=payload.seat_id,
        fare_id=payload.fare_id,
        sequence_number=payload.sequence_number,
        layover_minutes=payload.layover_minutes,
        price=fare.price,
        issue_date=date.today(),
    )
    db.add(ticket)
    db.commit()
    db.refresh(ticket)

    return TicketRead(
        ticket_id=ticket.ticket_id,
        booking_id=ticket.booking_id,
        schedule_id=ticket.schedule_id,
        seat_id=ticket.seat_id,
        fare_id=ticket.fare_id,
        flight_number=schedule.flight.flight_number,
        seat_number=seat.seat_number,
        price=ticket.price,
        issue_date=ticket.issue_date,
    )
