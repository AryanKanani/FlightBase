from __future__ import annotations

from datetime import date, datetime, timedelta
from decimal import Decimal
import random

from faker import Faker
from sqlalchemy.orm import Session

from app.models import (
    Aircraft,
    Airline,
    Airport,
    Booking,
    Crew,
    Fare,
    Flight,
    Passenger,
    Payment,
    Schedule,
    ScheduleCrew,
    Seat,
    SeatClass,
    Ticket,
)


fake = Faker()
Faker.seed(42)
random.seed(42)


def seed_database(db: Session) -> None:
    if db.query(Airline).first():
        return

    airlines = _create_airlines(db)
    airports = _create_airports(db)
    seat_classes = _create_seat_classes(db)
    aircraft = _create_aircraft(db, airlines)
    flights = _create_flights(db, airlines, airports)
    schedules = _create_schedules(db, flights, aircraft)
    seats = _create_seats(db, aircraft, seat_classes)
    fares = _create_fares(db, flights, seat_classes)
    crew_members = _create_crew(db)
    _assign_crew_to_schedules(db, schedules, crew_members)
    passengers = _create_passengers(db)
    _create_bookings_tickets_and_payments(db, passengers, schedules, seats, fares)
    db.commit()


def _create_airlines(db: Session) -> list[Airline]:
    airline_data = [
        ("SkyJet Airways", "SJ"),
        ("Nimbus Air", "NB"),
        ("AeroVista", "AV"),
    ]
    airlines = [Airline(name=name, iata_code=code) for name, code in airline_data]
    db.add_all(airlines)
    db.flush()
    return airlines


def _create_airports(db: Session) -> list[Airport]:
    airport_data = [
        ("Indira Gandhi International Airport", "Delhi", "India", "DEL"),
        ("Chhatrapati Shivaji Maharaj International Airport", "Mumbai", "India", "BOM"),
        ("Kempegowda International Airport", "Bengaluru", "India", "BLR"),
        ("Rajiv Gandhi International Airport", "Hyderabad", "India", "HYD"),
        ("Chennai International Airport", "Chennai", "India", "MAA"),
    ]
    airports = [
        Airport(name=name, city=city, country=country, iata_code=code)
        for name, city, country, code in airport_data
    ]
    db.add_all(airports)
    db.flush()
    return airports


def _create_seat_classes(db: Session) -> list[SeatClass]:
    seat_classes = [
        SeatClass(class_name="Economy", description="Standard cabin seating"),
        SeatClass(class_name="Business", description="Business cabin seating"),
        SeatClass(class_name="First", description="Premium first-class seating"),
    ]
    db.add_all(seat_classes)
    db.flush()
    return seat_classes


def _create_aircraft(db: Session, airlines: list[Airline]) -> list[Aircraft]:
    aircraft = [
        Aircraft(
            airline_id=airlines[0].airline_id,
            model="A320",
            manufacturer="Airbus",
            total_seats=180,
        ),
        Aircraft(
            airline_id=airlines[1].airline_id,
            model="B737",
            manufacturer="Boeing",
            total_seats=160,
        ),
        Aircraft(
            airline_id=airlines[2].airline_id,
            model="A321",
            manufacturer="Airbus",
            total_seats=200,
        ),
    ]
    db.add_all(aircraft)
    db.flush()
    return aircraft


def _create_flights(db: Session, airlines: list[Airline], airports: list[Airport]) -> list[Flight]:
    flight_specs = [
        (airlines[0], "SJ101", airports[0], airports[1]),
        (airlines[0], "SJ202", airports[1], airports[2]),
        (airlines[1], "NB303", airports[2], airports[3]),
        (airlines[1], "NB404", airports[3], airports[4]),
        (airlines[2], "AV505", airports[4], airports[0]),
    ]
    flights = [
        Flight(
            airline_id=airline.airline_id,
            flight_number=flight_number,
            origin_airport_id=origin.airport_id,
            destination_airport_id=destination.airport_id,
        )
        for airline, flight_number, origin, destination in flight_specs
    ]
    db.add_all(flights)
    db.flush()
    return flights


def _create_schedules(
    db: Session, flights: list[Flight], aircraft: list[Aircraft]
) -> list[Schedule]:
    base_departure = datetime.now().replace(hour=6, minute=0, second=0, microsecond=0)
    schedules: list[Schedule] = []

    for index, flight in enumerate(flights):
        departure_time = base_departure + timedelta(days=index, hours=index)
        arrival_time = departure_time + timedelta(hours=2)
        schedule = Schedule(
            flight_id=flight.flight_id,
            aircraft_id=aircraft[index % len(aircraft)].aircraft_id,
            departure_time=departure_time,
            arrival_time=arrival_time,
            status="Scheduled",
        )
        schedules.append(schedule)

    db.add_all(schedules)
    db.flush()
    return schedules


def _create_seats(
    db: Session, aircraft_list: list[Aircraft], seat_classes: list[SeatClass]
) -> list[Seat]:
    seats: list[Seat] = []

    for aircraft in aircraft_list:
        seats_created_for_aircraft = 0
        for row in range(1, 100):
            for seat_letter in ["A", "B", "C", "D", "E", "F"]:
                if seats_created_for_aircraft >= aircraft.total_seats:
                    break
                if row <= 2:
                    class_id = seat_classes[2].class_id
                elif row <= 4:
                    class_id = seat_classes[1].class_id
                else:
                    class_id = seat_classes[0].class_id

                seats.append(
                    Seat(
                        aircraft_id=aircraft.aircraft_id,
                        seat_number=f"{row}{seat_letter}",
                        class_id=class_id,
                    )
                )
                seats_created_for_aircraft += 1
            if seats_created_for_aircraft >= aircraft.total_seats:
                break

    db.add_all(seats)
    db.flush()
    return seats


def _create_fares(db: Session, flights: list[Flight], seat_classes: list[SeatClass]) -> list[Fare]:
    fares: list[Fare] = []
    class_prices = {
        "Economy": Decimal("4500.00"),
        "Business": Decimal("9000.00"),
        "First": Decimal("15000.00"),
    }

    for flight in flights:
        for seat_class in seat_classes:
            fares.append(
                Fare(
                    flight_id=flight.flight_id,
                    class_id=seat_class.class_id,
                    price=class_prices[seat_class.class_name] + Decimal(random.randint(0, 1500)),
                )
            )

    db.add_all(fares)
    db.flush()
    return fares


def _create_crew(db: Session) -> list[Crew]:
    roles = ["Pilot", "Co-Pilot", "Cabin Crew", "Cabin Crew", "Cabin Crew"]
    crew_members = [
        Crew(
            name=fake.name(),
            role=role,
            contact=fake.phone_number(),
        )
        for role in roles * 3
    ]
    db.add_all(crew_members)
    db.flush()
    return crew_members


def _assign_crew_to_schedules(
    db: Session, schedules: list[Schedule], crew_members: list[Crew]
) -> None:
    assignments: list[ScheduleCrew] = []
    crew_per_schedule = 3

    for index, schedule in enumerate(schedules):
        start = index * crew_per_schedule
        selected_crew = crew_members[start : start + crew_per_schedule]
        for crew in selected_crew:
            assignments.append(ScheduleCrew(schedule_id=schedule.schedule_id, crew_id=crew.crew_id))

    db.add_all(assignments)
    db.flush()


def _create_passengers(db: Session) -> list[Passenger]:
    passengers = [
        Passenger(
            name=fake.name(),
            email=fake.unique.email(),
            phone=fake.phone_number(),
            passport_no=fake.unique.bothify(text="??######"),
        )
        for _ in range(10)
    ]
    db.add_all(passengers)
    db.flush()
    return passengers


def _create_bookings_tickets_and_payments(
    db: Session,
    passengers: list[Passenger],
    schedules: list[Schedule],
    seats: list[Seat],
    fares: list[Fare],
) -> None:
    available_seats = seats[:]

    for passenger in passengers:
        schedule = random.choice(schedules)
        matching_fares = [fare for fare in fares if fare.flight_id == schedule.flight_id]
        chosen_fare = random.choice(matching_fares)
        matching_seat = next(
            seat
            for seat in available_seats
            if seat.aircraft_id == schedule.aircraft_id and seat.class_id == chosen_fare.class_id
        )
        available_seats.remove(matching_seat)

        booking = Booking(
            passenger_id=passenger.passenger_id,
            booking_date=date.today(),
            status="Confirmed",
            total_price=chosen_fare.price,
        )
        db.add(booking)
        db.flush()

        ticket = Ticket(
            booking_id=booking.booking_id,
            schedule_id=schedule.schedule_id,
            seat_id=matching_seat.seat_id,
            fare_id=chosen_fare.fare_id,
            sequence_number=1,
            layover_minutes=0,
            price=chosen_fare.price,
            issue_date=date.today(),
        )
        db.add(ticket)

        payment = Payment(
            booking_id=booking.booking_id,
            amount=chosen_fare.price,
            method=random.choice(["Card", "UPI", "Net Banking"]),
            payment_date=date.today(),
        )
        db.add(payment)

    db.flush()
