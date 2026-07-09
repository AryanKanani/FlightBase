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


class TicketBookingCreate(BaseModel):
    passenger_name: str
    email: str
    phone: str
    passport_no: str
    source: str
    destination: str
    travel_date: date
    seat_class: str
    payment_method: str


class BookingDetailRead(BaseModel):
    booking_id: int
    booking_date: date
    status: str
    passenger_id: int
    passenger_name: str
    email: str
    phone: str
    passport_no: str
    ticket_id: int
    flight_number: str
    source: str
    destination: str
    travel_date: date
    departure_time: str
    arrival_time: str
    seat_number: str
    seat_class: str
    ticket_price: Decimal
    payment_id: int
    payment_method: str
    payment_date: date
