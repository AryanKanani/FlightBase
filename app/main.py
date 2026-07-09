from fastapi import FastAPI

from app.api.airports import router as airports_router
from app.api.bookings import router as bookings_router
from app.api.fares import router as fares_router
from app.api.flights import router as flights_router
from app.api.passengers import router as passengers_router
from app.api.payments import router as payments_router
from app.api.schedules import router as schedules_router


app = FastAPI(title="Airline Management System API")

app.include_router(airports_router)
app.include_router(bookings_router)
app.include_router(fares_router)
app.include_router(flights_router)
app.include_router(passengers_router)
app.include_router(payments_router)
app.include_router(schedules_router)


@app.get("/health")
def health_check() -> dict[str, str]:
    return {"status": "ok"}
