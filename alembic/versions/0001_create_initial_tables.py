"""create initial tables"""

from alembic import op
import sqlalchemy as sa


revision = "0001_create_initial_tables"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "airline",
        sa.Column("airline_id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("iata_code", sa.String(length=10), nullable=False, unique=True),
    )

    op.create_table(
        "airport",
        sa.Column("airport_id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(length=120), nullable=False),
        sa.Column("city", sa.String(length=100), nullable=False),
        sa.Column("country", sa.String(length=100), nullable=False),
        sa.Column("iata_code", sa.String(length=10), nullable=False, unique=True),
    )

    op.create_table(
        "crew",
        sa.Column("crew_id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(length=120), nullable=False),
        sa.Column("role", sa.String(length=50), nullable=False),
        sa.Column("contact", sa.String(length=120), nullable=False),
    )

    op.create_table(
        "passenger",
        sa.Column("passenger_id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(length=120), nullable=False),
        sa.Column("email", sa.String(length=120), nullable=False, unique=True),
        sa.Column("phone", sa.String(length=30), nullable=False),
        sa.Column("passport_no", sa.String(length=30), nullable=False, unique=True),
    )

    op.create_table(
        "seat_class",
        sa.Column("class_id", sa.Integer(), primary_key=True),
        sa.Column("class_name", sa.String(length=50), nullable=False, unique=True),
        sa.Column("description", sa.String(length=255), nullable=True),
    )

    op.create_table(
        "aircraft",
        sa.Column("aircraft_id", sa.Integer(), primary_key=True),
        sa.Column("airline_id", sa.Integer(), sa.ForeignKey("airline.airline_id"), nullable=False),
        sa.Column("model", sa.String(length=100), nullable=False),
        sa.Column("manufacturer", sa.String(length=100), nullable=False),
        sa.Column("total_seats", sa.Integer(), nullable=False),
    )

    op.create_table(
        "flight",
        sa.Column("flight_id", sa.Integer(), primary_key=True),
        sa.Column("airline_id", sa.Integer(), sa.ForeignKey("airline.airline_id"), nullable=False),
        sa.Column("flight_number", sa.String(length=20), nullable=False, unique=True),
        sa.Column("origin_airport_id", sa.Integer(), sa.ForeignKey("airport.airport_id"), nullable=False),
        sa.Column("destination_airport_id", sa.Integer(), sa.ForeignKey("airport.airport_id"), nullable=False),
    )

    op.create_table(
        "booking",
        sa.Column("booking_id", sa.Integer(), primary_key=True),
        sa.Column("passenger_id", sa.Integer(), sa.ForeignKey("passenger.passenger_id"), nullable=False),
        sa.Column("booking_date", sa.Date(), nullable=False),
        sa.Column("status", sa.String(length=30), nullable=False),
        sa.Column("total_price", sa.Numeric(10, 2), nullable=False),
    )

    op.create_table(
        "fare",
        sa.Column("fare_id", sa.Integer(), primary_key=True),
        sa.Column("flight_id", sa.Integer(), sa.ForeignKey("flight.flight_id"), nullable=False),
        sa.Column("class_id", sa.Integer(), sa.ForeignKey("seat_class.class_id"), nullable=False),
        sa.Column("price", sa.Numeric(10, 2), nullable=False),
        sa.UniqueConstraint("flight_id", "class_id", name="uq_flight_class_fare"),
    )

    op.create_table(
        "schedule",
        sa.Column("schedule_id", sa.Integer(), primary_key=True),
        sa.Column("flight_id", sa.Integer(), sa.ForeignKey("flight.flight_id"), nullable=False),
        sa.Column("aircraft_id", sa.Integer(), sa.ForeignKey("aircraft.aircraft_id"), nullable=False),
        sa.Column("departure_time", sa.DateTime(), nullable=False),
        sa.Column("arrival_time", sa.DateTime(), nullable=False),
        sa.Column("status", sa.String(length=30), nullable=False),
    )

    op.create_table(
        "seat",
        sa.Column("seat_id", sa.Integer(), primary_key=True),
        sa.Column("aircraft_id", sa.Integer(), sa.ForeignKey("aircraft.aircraft_id"), nullable=False),
        sa.Column("seat_number", sa.String(length=10), nullable=False),
        sa.Column("class_id", sa.Integer(), sa.ForeignKey("seat_class.class_id"), nullable=False),
        sa.UniqueConstraint("aircraft_id", "seat_number", name="uq_aircraft_seat_number"),
    )

    op.create_table(
        "payment",
        sa.Column("payment_id", sa.Integer(), primary_key=True),
        sa.Column("booking_id", sa.Integer(), sa.ForeignKey("booking.booking_id"), nullable=False),
        sa.Column("amount", sa.Numeric(10, 2), nullable=False),
        sa.Column("method", sa.String(length=30), nullable=False),
        sa.Column("status", sa.String(length=30), nullable=False),
        sa.Column("payment_date", sa.Date(), nullable=False),
    )

    op.create_table(
        "schedule_crew",
        sa.Column("schedule_id", sa.Integer(), sa.ForeignKey("schedule.schedule_id"), primary_key=True),
        sa.Column("crew_id", sa.Integer(), sa.ForeignKey("crew.crew_id"), primary_key=True),
    )

    op.create_table(
        "ticket",
        sa.Column("ticket_id", sa.Integer(), primary_key=True),
        sa.Column("booking_id", sa.Integer(), sa.ForeignKey("booking.booking_id"), nullable=False),
        sa.Column("schedule_id", sa.Integer(), sa.ForeignKey("schedule.schedule_id"), nullable=False),
        sa.Column("seat_id", sa.Integer(), sa.ForeignKey("seat.seat_id"), nullable=False),
        sa.Column("fare_id", sa.Integer(), sa.ForeignKey("fare.fare_id"), nullable=False),
        sa.Column("sequence_number", sa.Integer(), nullable=False),
        sa.Column("layover_minutes", sa.Integer(), nullable=False),
        sa.Column("price", sa.Numeric(10, 2), nullable=False),
        sa.Column("issue_date", sa.Date(), nullable=False),
    )


def downgrade() -> None:
    op.drop_table("ticket")
    op.drop_table("schedule_crew")
    op.drop_table("payment")
    op.drop_table("seat")
    op.drop_table("schedule")
    op.drop_table("fare")
    op.drop_table("booking")
    op.drop_table("flight")
    op.drop_table("aircraft")
    op.drop_table("seat_class")
    op.drop_table("passenger")
    op.drop_table("crew")
    op.drop_table("airport")
    op.drop_table("airline")
