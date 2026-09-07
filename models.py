"""Transaction model and validation for the expense tracker."""

from __future__ import annotations

from dataclasses import dataclass, asdict
from datetime import datetime

VALID_TYPES = ("income", "expense")


class ValidationError(Exception):
    """Raised when transaction data fails validation."""


@dataclass
class Transaction:
    id: str
    type: str
    amount: float
    category: str
    date: str  # ISO format: YYYY-MM-DD
    note: str = ""

    def to_dict(self) -> dict:
        return asdict(self)

    @staticmethod
    def from_dict(data: dict) -> "Transaction":
        return Transaction(
            id=data["id"],
            type=data["type"],
            amount=float(data["amount"]),
            category=data["category"],
            date=data["date"],
            note=data.get("note", "") or "",
        )


def validate_type(value: str) -> str:
    value = (value or "").strip().lower()
    if value not in VALID_TYPES:
        raise ValidationError(f"Type must be 'income' or 'expense', got '{value}'")
    return value


def validate_amount(value) -> float:
    try:
        amount = float(value)
    except (TypeError, ValueError):
        raise ValidationError(f"Amount must be a number, got '{value}'")
    if amount <= 0:
        raise ValidationError(f"Amount must be positive, got {amount}")
    return amount


def validate_category(value: str) -> str:
    value = (value or "").strip()
    if not value:
        raise ValidationError("Category cannot be empty")
    return value


def validate_date(value: str) -> str:
    value = (value or "").strip()
    try:
        parsed = datetime.strptime(value, "%Y-%m-%d").date()
    except ValueError:
        raise ValidationError(f"Date must be in YYYY-MM-DD format, got '{value}'")
    return parsed.isoformat()


def validate_note(value: str) -> str:
    return (value or "").strip()
