from fastapi import FastAPI

from app.api.airports import router as airports_router
from app.api.flights import router as flights_router


app = FastAPI(title="Airline Management System API")

app.include_router(airports_router)
app.include_router(flights_router)


@app.get("/health")
def health_check() -> dict[str, str]:
    return {"status": "ok"}
