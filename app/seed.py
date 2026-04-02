from __future__ import annotations

from datetime import date, timedelta

from sqlalchemy import select

from app.core.security import get_password_hash
from app.database import SessionLocal, create_all
from app.models.record import FinancialRecord, RecordType
from app.models.user import User, UserRole


def seed_users() -> dict[str, User]:
    users_to_seed = [
        {
            "email": "admin@finance.com",
            "password": "Admin1234",
            "full_name": "Finance Admin",
            "role": UserRole.admin,
        },
        {
            "email": "analyst@finance.com",
            "password": "Analyst1234",
            "full_name": "Finance Analyst",
            "role": UserRole.analyst,
        },
        {
            "email": "viewer@finance.com",
            "password": "Viewer1234",
            "full_name": "Finance Viewer",
            "role": UserRole.viewer,
        },
    ]

    user_map: dict[str, User] = {}
    with SessionLocal() as db:
        for user_data in users_to_seed:
            existing = db.execute(select(User).where(User.email == user_data["email"])).scalar_one_or_none()
            if existing is None:
                existing = User(
                    email=user_data["email"],
                    hashed_password=get_password_hash(user_data["password"]),
                    full_name=user_data["full_name"],
                    role=user_data["role"],
                )
                db.add(existing)
                db.commit()
                db.refresh(existing)
            user_map[user_data["email"]] = existing
    return user_map


def seed_records(user_map: dict[str, User]) -> None:
    today = date.today()
    sample_records = [
        (8200.0, RecordType.income, "salary", 12, "Monthly salary payout", "admin@finance.com"),
        (1200.0, RecordType.expense, "rent", 10, "Downtown apartment rent", "admin@finance.com"),
        (360.0, RecordType.expense, "utilities", 8, "Electricity and internet", "admin@finance.com"),
        (240.0, RecordType.expense, "food", 6, "Weekly groceries", "viewer@finance.com"),
        (1800.0, RecordType.income, "freelance", 20, "Mobile app consulting", "analyst@finance.com"),
        (8150.0, RecordType.income, "salary", 35, "Monthly salary payout", "admin@finance.com"),
        (1250.0, RecordType.expense, "rent", 33, "Downtown apartment rent", "admin@finance.com"),
        (395.0, RecordType.expense, "utilities", 31, "Water and electricity", "analyst@finance.com"),
        (285.0, RecordType.expense, "food", 28, "Team lunch and groceries", "viewer@finance.com"),
        (2400.0, RecordType.income, "freelance", 45, "E-commerce integration project", "analyst@finance.com"),
        (8300.0, RecordType.income, "salary", 62, "Monthly salary payout", "admin@finance.com"),
        (1300.0, RecordType.expense, "rent", 60, "Downtown apartment rent", "admin@finance.com"),
        (410.0, RecordType.expense, "utilities", 58, "Utility bill bundle", "analyst@finance.com"),
        (320.0, RecordType.expense, "food", 55, "Meal delivery and groceries", "viewer@finance.com"),
        (3100.0, RecordType.income, "freelance", 78, "Quarterly advisory retainer", "analyst@finance.com"),
        (8450.0, RecordType.income, "salary", 95, "Monthly salary payout", "admin@finance.com"),
        (1350.0, RecordType.expense, "rent", 93, "Downtown apartment rent", "admin@finance.com"),
        (450.0, RecordType.expense, "utilities", 90, "Utilities catch-up payment", "analyst@finance.com"),
    ]

    with SessionLocal() as db:
        for amount, record_type, category, days_ago, notes, owner_email in sample_records:
            record_date = today - timedelta(days=days_ago)
            existing = db.execute(
                select(FinancialRecord).where(
                    FinancialRecord.amount == amount,
                    FinancialRecord.type == record_type,
                    FinancialRecord.category == category,
                    FinancialRecord.date == record_date,
                    FinancialRecord.notes == notes,
                )
            ).scalar_one_or_none()

            if existing is None:
                db.add(
                    FinancialRecord(
                        amount=amount,
                        type=record_type,
                        category=category,
                        date=record_date,
                        notes=notes,
                        created_by=user_map[owner_email].id,
                    )
                )

        db.commit()


def main() -> None:
    create_all()
    user_map = seed_users()
    seed_records(user_map)
    print("Seed completed successfully.")


if __name__ == "__main__":
    main()
