from datetime import date
from decimal import Decimal

from pydantic import BaseModel


class ReservationCreate(BaseModel):
    passenger_id: int
    schedule_id: int
    seat_id: int
    fare_id: int
    payment_method: str
    sequence_number: int = 1
    layover_minutes: int = 0


class ReservationRead(BaseModel):
    booking_id: int
    ticket_id: int
    payment_id: int
    passenger_id: int
    passenger_name: str
    schedule_id: int
    flight_number: str
    seat_id: int
    seat_number: str
    fare_id: int
    seat_class: str
    total_price: Decimal
    payment_method: str
    booking_date: date
    issue_date: date
    payment_date: date
