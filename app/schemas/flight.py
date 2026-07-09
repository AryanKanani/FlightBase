from pydantic import BaseModel, ConfigDict
from datetime import date
from decimal import Decimal


class FlightRead(BaseModel):
    flight_id: int
    flight_number: str
    airline_name: str
    origin_airport_name: str
    origin_airport_code: str
    destination_airport_name: str
    destination_airport_code: str

    model_config = ConfigDict(from_attributes=True)


class FlightSearchRead(BaseModel):
    schedule_id: int
    flight_id: int
    flight_number: str
    airline_name: str
    source: str
    destination: str
    travel_date: date
    departure_time: str
    arrival_time: str
    seat_class: str
    price: Decimal
    available_seats: int
