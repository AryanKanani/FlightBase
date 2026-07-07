from app.db.session import SessionLocal
from app.services.seed_data import seed_database


def main() -> None:
    db = SessionLocal()
    try:
        seed_database(db)
        print("Database seeded successfully.")
    finally:
        db.close()


if __name__ == "__main__":
    main()
