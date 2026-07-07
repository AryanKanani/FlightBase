from pydantic import BaseModel, ConfigDict


class AirportCreate(BaseModel):
    name: str
    city: str
    country: str
    iata_code: str


class AirportRead(BaseModel):
    airport_id: int
    name: str
    city: str
    country: str
    iata_code: str

    model_config = ConfigDict(from_attributes=True)
