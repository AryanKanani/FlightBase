from pydantic import BaseModel, ConfigDict


class PassengerCreate(BaseModel):
    name: str
    email: str
    phone: str
    passport_no: str


class PassengerRead(BaseModel):
    passenger_id: int
    name: str
    email: str
    phone: str
    passport_no: str

    model_config = ConfigDict(from_attributes=True)
