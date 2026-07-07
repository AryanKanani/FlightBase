from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import Date, DateTime, ForeignKey, Integer, Numeric, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class Airline(Base):
    __tablename__ = "airline"

    airline_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    iata_code: Mapped[str] = mapped_column(String(10), unique=True, nullable=False)

    aircraft: Mapped[list["Aircraft"]] = relationship("Aircraft", back_populates="airline")
    flights: Mapped[list["Flight"]] = relationship("Flight", back_populates="airline")


class Airport(Base):
    __tablename__ = "airport"

    airport_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    city: Mapped[str] = mapped_column(String(100), nullable=False)
    country: Mapped[str] = mapped_column(String(100), nullable=False)
    iata_code: Mapped[str] = mapped_column(String(10), unique=True, nullable=False)

    origin_flights: Mapped[list["Flight"]] = relationship(
        "Flight",
        back_populates="origin_airport",
        foreign_keys="Flight.origin_airport_id",
    )
    destination_flights: Mapped[list["Flight"]] = relationship(
        "Flight",
        back_populates="destination_airport",
        foreign_keys="Flight.destination_airport_id",
    )


class Aircraft(Base):
    __tablename__ = "aircraft"

    aircraft_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    airline_id: Mapped[int] = mapped_column(ForeignKey("airline.airline_id"), nullable=False)
    model: Mapped[str] = mapped_column(String(100), nullable=False)
    manufacturer: Mapped[str] = mapped_column(String(100), nullable=False)
    total_seats: Mapped[int] = mapped_column(Integer, nullable=False)

    airline: Mapped["Airline"] = relationship("Airline", back_populates="aircraft")
    seats: Mapped[list["Seat"]] = relationship("Seat", back_populates="aircraft")
    schedules: Mapped[list["Schedule"]] = relationship("Schedule", back_populates="aircraft")


class Flight(Base):
    __tablename__ = "flight"

    flight_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    airline_id: Mapped[int] = mapped_column(ForeignKey("airline.airline_id"), nullable=False)
    flight_number: Mapped[str] = mapped_column(String(20), unique=True, nullable=False)
    origin_airport_id: Mapped[int] = mapped_column(ForeignKey("airport.airport_id"), nullable=False)
    destination_airport_id: Mapped[int] = mapped_column(ForeignKey("airport.airport_id"), nullable=False)

    airline: Mapped["Airline"] = relationship("Airline", back_populates="flights")
    origin_airport: Mapped["Airport"] = relationship(
        "Airport",
        back_populates="origin_flights",
        foreign_keys=[origin_airport_id],
    )
    destination_airport: Mapped["Airport"] = relationship(
        "Airport",
        back_populates="destination_flights",
        foreign_keys=[destination_airport_id],
    )
    schedules: Mapped[list["Schedule"]] = relationship("Schedule", back_populates="flight")
    fares: Mapped[list["Fare"]] = relationship("Fare", back_populates="flight")


class SeatClass(Base):
    __tablename__ = "seat_class"

    class_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    class_name: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    description: Mapped[str | None] = mapped_column(String(255))

    seats: Mapped[list["Seat"]] = relationship("Seat", back_populates="seat_class")
    fares: Mapped[list["Fare"]] = relationship("Fare", back_populates="seat_class")


class Passenger(Base):
    __tablename__ = "passenger"

    passenger_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    email: Mapped[str] = mapped_column(String(120), unique=True, nullable=False)
    phone: Mapped[str] = mapped_column(String(30), nullable=False)
    passport_no: Mapped[str] = mapped_column(String(30), unique=True, nullable=False)

    bookings: Mapped[list["Booking"]] = relationship("Booking", back_populates="passenger")


class Crew(Base):
    __tablename__ = "crew"

    crew_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    role: Mapped[str] = mapped_column(String(50), nullable=False)
    contact: Mapped[str] = mapped_column(String(120), nullable=False)

    schedule_links: Mapped[list["ScheduleCrew"]] = relationship("ScheduleCrew", back_populates="crew")


class Schedule(Base):
    __tablename__ = "schedule"

    schedule_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    flight_id: Mapped[int] = mapped_column(ForeignKey("flight.flight_id"), nullable=False)
    aircraft_id: Mapped[int] = mapped_column(ForeignKey("aircraft.aircraft_id"), nullable=False)
    departure_time: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    arrival_time: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    status: Mapped[str] = mapped_column(String(30), nullable=False)

    flight: Mapped["Flight"] = relationship("Flight", back_populates="schedules")
    aircraft: Mapped["Aircraft"] = relationship("Aircraft", back_populates="schedules")
    crew_links: Mapped[list["ScheduleCrew"]] = relationship("ScheduleCrew", back_populates="schedule")
    tickets: Mapped[list["Ticket"]] = relationship("Ticket", back_populates="schedule")


class Seat(Base):
    __tablename__ = "seat"
    __table_args__ = (UniqueConstraint("aircraft_id", "seat_number", name="uq_aircraft_seat_number"),)

    seat_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    aircraft_id: Mapped[int] = mapped_column(ForeignKey("aircraft.aircraft_id"), nullable=False)
    seat_number: Mapped[str] = mapped_column(String(10), nullable=False)
    class_id: Mapped[int] = mapped_column(ForeignKey("seat_class.class_id"), nullable=False)

    aircraft: Mapped["Aircraft"] = relationship("Aircraft", back_populates="seats")
    seat_class: Mapped["SeatClass"] = relationship("SeatClass", back_populates="seats")
    tickets: Mapped[list["Ticket"]] = relationship("Ticket", back_populates="seat")


class Fare(Base):
    __tablename__ = "fare"
    __table_args__ = (UniqueConstraint("flight_id", "class_id", name="uq_flight_class_fare"),)

    fare_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    flight_id: Mapped[int] = mapped_column(ForeignKey("flight.flight_id"), nullable=False)
    class_id: Mapped[int] = mapped_column(ForeignKey("seat_class.class_id"), nullable=False)
    price: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)

    flight: Mapped["Flight"] = relationship("Flight", back_populates="fares")
    seat_class: Mapped["SeatClass"] = relationship("SeatClass", back_populates="fares")
    tickets: Mapped[list["Ticket"]] = relationship("Ticket", back_populates="fare")


class Booking(Base):
    __tablename__ = "booking"

    booking_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    passenger_id: Mapped[int] = mapped_column(ForeignKey("passenger.passenger_id"), nullable=False)
    booking_date: Mapped[date] = mapped_column(Date, nullable=False)
    status: Mapped[str] = mapped_column(String(30), nullable=False)
    total_price: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)

    passenger: Mapped["Passenger"] = relationship("Passenger", back_populates="bookings")
    tickets: Mapped[list["Ticket"]] = relationship("Ticket", back_populates="booking")
    payments: Mapped[list["Payment"]] = relationship("Payment", back_populates="booking")


class Ticket(Base):
    __tablename__ = "ticket"

    ticket_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    booking_id: Mapped[int] = mapped_column(ForeignKey("booking.booking_id"), nullable=False)
    schedule_id: Mapped[int] = mapped_column(ForeignKey("schedule.schedule_id"), nullable=False)
    seat_id: Mapped[int] = mapped_column(ForeignKey("seat.seat_id"), nullable=False)
    fare_id: Mapped[int] = mapped_column(ForeignKey("fare.fare_id"), nullable=False)
    sequence_number: Mapped[int] = mapped_column(Integer, nullable=False)
    layover_minutes: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    price: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    issue_date: Mapped[date] = mapped_column(Date, nullable=False)

    booking: Mapped["Booking"] = relationship("Booking", back_populates="tickets")
    schedule: Mapped["Schedule"] = relationship("Schedule", back_populates="tickets")
    seat: Mapped["Seat"] = relationship("Seat", back_populates="tickets")
    fare: Mapped["Fare"] = relationship("Fare", back_populates="tickets")


class Payment(Base):
    __tablename__ = "payment"

    payment_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    booking_id: Mapped[int] = mapped_column(ForeignKey("booking.booking_id"), nullable=False)
    amount: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    method: Mapped[str] = mapped_column(String(30), nullable=False)
    payment_date: Mapped[date] = mapped_column(Date, nullable=False)

    booking: Mapped["Booking"] = relationship("Booking", back_populates="payments")


class ScheduleCrew(Base):
    __tablename__ = "schedule_crew"

    schedule_id: Mapped[int] = mapped_column(ForeignKey("schedule.schedule_id"), primary_key=True)
    crew_id: Mapped[int] = mapped_column(ForeignKey("crew.crew_id"), primary_key=True)

    schedule: Mapped["Schedule"] = relationship("Schedule", back_populates="crew_links")
    crew: Mapped["Crew"] = relationship("Crew", back_populates="schedule_links")
