from datetime import date
from decimal import Decimal

from pydantic import BaseModel


class PaymentCreate(BaseModel):
    booking_id: int
    amount: Decimal
    method: str


class PaymentRead(BaseModel):
    payment_id: int
    booking_id: int
    amount: Decimal
    method: str
    payment_date: date
