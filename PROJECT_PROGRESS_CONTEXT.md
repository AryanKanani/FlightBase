# FlightBase Project Context

## Project Summary

This project is an airline management backend called `FlightBase`.

Current tech stack:

- `FastAPI`
- `PostgreSQL`
- `SQLAlchemy`
- `Alembic`
- `Faker`

The goal is to build a backend for an airline reservation/management system based on the user's ERD.

The user prefers:

- beginner-friendly explanations
- small step-by-step changes
- simple but efficient folder structure
- fake seed/demo data using `Faker`
- fake payments only
- payment records should represent completed payments only, with no payment status column

## Current Folder Structure

```text
DBMS/
├── alembic/
├── app/
│   ├── api/
│   ├── core/
│   ├── db/
│   ├── models/
│   ├── schemas/
│   └── services/
├── .env.example
├── .gitignore
├── alembic.ini
├── README.md
├── requirements.txt
├── seed.py
└── PROJECT_PROGRESS_CONTEXT.md
```

## What Has Been Implemented

### 1. Base Project Setup

Created:

- FastAPI app entrypoint in `app/main.py`
- project package folders
- `requirements.txt`
- `.gitignore`
- `README.md`

There is a simple health endpoint:

- `GET /health`

### 2. PostgreSQL and Database Setup

Created:

- `app/core/config.py`
- `app/db/base.py`
- `app/db/session.py`
- `.env.example`

Purpose:

- load `DATABASE_URL` from `.env`
- create SQLAlchemy engine
- create database session dependency

### 3. SQLAlchemy Models Based on ERD

Main model file:

- `app/models/entities.py`

Models currently implemented:

- `Airline`
- `Airport`
- `Aircraft`
- `Flight`
- `SeatClass`
- `Seat`
- `Fare`
- `Crew`
- `Schedule`
- `ScheduleCrew`
- `Passenger`
- `Booking`
- `Ticket`
- `Payment`

Important notes:

- `Payment` has no `status` field
- payment record means payment is completed
- unique constraints added for important fields such as:
  - airline IATA code
  - airport IATA code
  - flight number
  - seat number per aircraft
  - fare per flight/class

### 4. Alembic Migration Setup

Created:

- `alembic.ini`
- `alembic/env.py`
- `alembic/script.py.mako`
- `alembic/versions/0001_create_initial_tables.py`

Purpose:

- versioned database schema creation
- initial migration for all tables

### 5. Faker Seed System

Created:

- `app/services/seed_data.py`
- `seed.py`

What seed system currently creates:

- airlines
- airports
- seat classes
- aircraft
- flights
- schedules
- seats
- fares
- crew members
- passengers
- bookings
- tickets
- payments

Important payment rule:

- fake payments are created as completed payments only
- no pending/failed payment status field

### 6. Implemented API Modules

#### Airports

Files:

- `app/api/airports.py`
- `app/schemas/airport.py`

Endpoints:

- `GET /airports/`
- `POST /airports/`

Behavior:

- lists airports
- creates airport
- checks duplicate `iata_code`

#### Flights

Files:

- `app/api/flights.py`
- `app/schemas/flight.py`

Endpoints:

- `GET /flights/`
- `GET /flights/{flight_id}`

Behavior:

- returns readable flight data including airline and airport names/codes

#### Schedules

Files:

- `app/api/schedules.py`
- `app/schemas/schedule.py`

Endpoints:

- `GET /schedules/`
- `GET /schedules/{schedule_id}`

Behavior:

- returns flight number, aircraft model, departure time, arrival time, and status

#### Fares

Files:

- `app/api/fares.py`
- `app/schemas/fare.py`

Endpoints:

- `GET /fares/`
- `GET /fares/{fare_id}`

Behavior:

- returns price by flight and seat class

#### Passengers

Files:

- `app/api/passengers.py`
- `app/schemas/passenger.py`

Endpoints:

- `GET /passengers/`
- `POST /passengers/`

Behavior:

- creates passenger
- lists passengers
- checks duplicate email
- checks duplicate passport number

#### Bookings

Files:

- `app/api/bookings.py`
- `app/schemas/booking.py`

Endpoints:

- `GET /bookings/`
- `POST /bookings/`

Behavior:

- creates simple booking for existing passenger
- auto-sets:
  - `booking_date`
  - `status = "Confirmed"`

Current limitation:

- booking creation is still simple and does not yet create ticket/payment automatically

#### Payments

Files:

- `app/api/payments.py`
- `app/schemas/payment.py`

Endpoints:

- `GET /payments/`
- `POST /payments/`

Behavior:

- creates payment for an existing booking
- auto-sets `payment_date`
- payment means completed payment

Current limitation:

- no duplicate-payment prevention yet
- does not compare payment amount to booking total

#### Tickets

Files:

- `app/api/tickets.py`
- `app/schemas/ticket.py`

Endpoints:

- `GET /tickets/`
- `POST /tickets/`

Behavior:

- creates ticket linked to booking, schedule, seat, and fare
- auto-sets:
  - `price` from fare
  - `issue_date`
- prevents assigning the same seat twice for the same schedule

Current limitation:

- does not yet verify that:
  - seat belongs to the aircraft used in the selected schedule
  - fare belongs to the flight used by the selected schedule

## Current Main App Routing

`app/main.py` currently registers:

- airports
- bookings
- fares
- flights
- passengers
- payments
- schedules
- tickets

## Important Design Decisions Already Made

1. Python is being used because the backend stack is `FastAPI + SQLAlchemy`.
2. PostgreSQL is the database.
3. Faker is used for seeding and fake payments.
4. Folder structure should stay simple, not over-engineered.
5. Explanations should stay beginner-friendly.
6. Payment records should not have a status field.
7. Stepwise development is preferred, but the user may commit multiple steps together later.

## Things Not Yet Done

These are still pending:

- install dependencies locally in a virtual environment
- create `.env`
- run Alembic migration
- run seed script
- run FastAPI server locally
- test APIs in Swagger/Postman
- create smarter transactional booking flow
- add stronger validation between linked tables
- add auth if needed later
- add tests

## Recommended Next Steps

### Near-Term Next Step

Build a smarter reservation endpoint that creates the full reservation flow in one request.

Recommended behavior:

- input:
  - `passenger_id`
  - `schedule_id`
  - `seat_id`
  - `fare_id`
  - `payment_method`
- backend should:
  - validate passenger
  - validate schedule
  - validate seat
  - validate fare
  - ensure seat belongs to aircraft of that schedule
  - ensure fare belongs to the flight of that schedule
  - ensure seat class matches fare class
  - ensure seat is not already booked on that schedule
  - create booking
  - create payment
  - create ticket
  - do all of it in one transaction

This would be the best next feature because it connects the main airline workflow end-to-end.

### After That

Recommended order:

1. Add combined reservation endpoint/service
2. Add booking detail endpoint showing passenger, ticket, payment
3. Add ticket lookup by booking or ticket id
4. Add better schedule/flight filtering
5. Add seat availability endpoint for a schedule
6. Add admin CRUD for airlines, aircraft, crew
7. Add validation and business rules cleanup
8. Add tests
9. Add authentication/authorization if needed

## Suggested Validation Improvements

These are good next validation upgrades:

1. Prevent payment amount mismatch with booking total
2. Prevent multiple payments for same booking unless explicitly allowed
3. Ensure seat belongs to selected schedule's aircraft
4. Ensure fare belongs to selected schedule's flight
5. Ensure fare class matches seat class
6. Possibly auto-calculate booking total from fare instead of taking manual price input

## Suggested Testing Flow Once Environment Is Ready

After local setup is done, test in this order:

1. `GET /health`
2. `GET /airports/`
3. `POST /airports/`
4. `GET /flights/`
5. `GET /schedules/`
6. `GET /fares/`
7. `POST /passengers/`
8. `POST /bookings/`
9. `POST /payments/`
10. `POST /tickets/`

Then later replace steps 8-10 with a smarter single reservation endpoint.

## Local Setup Still Needed

Another LLM or developer should help the user do these steps when ready:

1. Create virtual environment in project root
2. Activate virtual environment
3. Install dependencies from `requirements.txt`
4. Create `.env` using `.env.example`
5. Create PostgreSQL database `airline_management`
6. Run:

```powershell
alembic upgrade head
```

7. Run:

```powershell
python seed.py
```

8. Start server:

```powershell
uvicorn app.main:app --reload
```

9. Open:

```text
http://127.0.0.1:8000/docs
```

## Notes For Another LLM

- Do not radically change the folder structure unless necessary.
- Keep explanations beginner-friendly.
- Prefer small, meaningful changes.
- The user is okay committing multiple steps later, so do not block progress just because git status is dirty.
- Keep payment model simple.
- Preserve PostgreSQL + FastAPI + SQLAlchemy + Alembic + Faker stack.
