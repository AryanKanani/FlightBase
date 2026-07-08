from pydantic import BaseModel, ConfigDict


class FlightRead(BaseModel):
    flight_id: int
    flight_number: str
    airline_name: str
    origin_airport_name: str
    origin_airport_code: str
    destination_airport_name: str
    destination_airport_code: str

    model_config = ConfigDict(from_attributes=True)
