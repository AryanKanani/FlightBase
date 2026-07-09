from datetime import date
from decimal import Decimal

from pydantic import BaseModel


class TicketCreate(BaseModel):
    booking_id: int
    schedule_id: int
    seat_id: int
    fare_id: int
    sequence_number: int = 1
    layover_minutes: int = 0


class TicketRead(BaseModel):
    ticket_id: int
    booking_id: int
    schedule_id: int
    seat_id: int
    fare_id: int
    flight_number: str
    seat_number: str
    price: Decimal
    issue_date: date
