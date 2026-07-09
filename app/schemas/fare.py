from decimal import Decimal

from pydantic import BaseModel


class FareRead(BaseModel):
    fare_id: int
    flight_number: str
    seat_class: str
    price: Decimal
