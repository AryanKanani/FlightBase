from datetime import date
from decimal import Decimal

from pydantic import BaseModel


class BookingCreate(BaseModel):
    passenger_id: int
    total_price: Decimal


class BookingRead(BaseModel):
    booking_id: int
    passenger_id: int
    passenger_name: str
    booking_date: date
    status: str
    total_price: Decimal
