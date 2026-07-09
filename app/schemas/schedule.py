from datetime import datetime

from pydantic import BaseModel


class ScheduleRead(BaseModel):
    schedule_id: int
    flight_number: str
    aircraft_model: str
    departure_time: datetime
    arrival_time: datetime
    status: str
