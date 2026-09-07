"""CSV-backed storage and business logic for transactions.

This is the data layer. It has no knowledge of any UI (CLI today,
desktop GUI later) so it can be reused as-is when the interface changes.
"""

from __future__ import annotations

import csv
import os
import uuid
from typing import Optional

from models import (
    Transaction,
    ValidationError,
    validate_type,
    validate_amount,
    validate_category,
    validate_date,
    validate_note,
)

STORAGE_DIR = os.path.join(os.path.dirname(__file__), "storage")
CSV_PATH = os.path.join(STORAGE_DIR, "transactions.csv")

FIELDNAMES = ["id", "type", "amount", "category", "date", "note"]


def ensure_storage_exists() -> None:
    """Create the storage folder/CSV with a header if they don't exist yet."""
    os.makedirs(STORAGE_DIR, exist_ok=True)
    if not os.path.exists(CSV_PATH):
        with open(CSV_PATH, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=FIELDNAMES)
            writer.writeheader()


def load_transactions() -> list[Transaction]:
    """Read all transactions from the CSV. Corrupted rows are skipped, not fatal."""
    ensure_storage_exists()
    transactions = []
    try:
        with open(CSV_PATH, "r", newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                try:
                    transactions.append(Transaction.from_dict(row))
                except (KeyError, ValueError, TypeError):
                    print(f"Warning: skipping corrupted row: {row}")
    except OSError as e:
        raise OSError(f"Could not read {CSV_PATH}: {e}") from e
    return transactions


def save_transactions(transactions: list[Transaction]) -> None:
    """Overwrite the CSV with the given list of transactions."""
    ensure_storage_exists()
    try:
        with open(CSV_PATH, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=FIELDNAMES)
            writer.writeheader()
            for t in transactions:
                writer.writerow(t.to_dict())
    except OSError as e:
        raise OSError(f"Could not write {CSV_PATH}: {e}") from e


def add_transaction(type_: str, amount, category: str, date: str, note: str = "") -> Transaction:
    """Validate and add a new transaction, saving it to disk. Raises ValidationError on bad input."""
    transactions = load_transactions()
    existing_ids = {t.id for t in transactions}

    new_transaction = Transaction(
        id=_generate_id(existing_ids),
        type=validate_type(type_),
        amount=validate_amount(amount),
        category=validate_category(category),
        date=validate_date(date),
        note=validate_note(note),
    )
    transactions.append(new_transaction)
    save_transactions(transactions)
    return new_transaction


def update_transaction(transaction_id: str, **fields) -> Transaction:
    """Update one or more fields on an existing transaction by id.

    Example: update_transaction(t.id, amount=25, note="corrected")
    """
    transactions = load_transactions()
    target = next((t for t in transactions if t.id == transaction_id), None)
    if target is None:
        raise ValidationError(f"No transaction with id '{transaction_id}'")

    if "type" in fields:
        target.type = validate_type(fields["type"])
    if "amount" in fields:
        target.amount = validate_amount(fields["amount"])
    if "category" in fields:
        target.category = validate_category(fields["category"])
    if "date" in fields:
        target.date = validate_date(fields["date"])
    if "note" in fields:
        target.note = validate_note(fields["note"])

    save_transactions(transactions)
    return target


def delete_transaction(transaction_id: str) -> bool:
    """Remove a transaction by id. Returns True if something was actually deleted."""
    transactions = load_transactions()
    remaining = [t for t in transactions if t.id != transaction_id]
    if len(remaining) == len(transactions):
        return False
    save_transactions(remaining)
    return True


def get_transactions(
    type_: Optional[str] = None,
    category: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
) -> list[Transaction]:
    """Retrieve transactions, optionally filtered by type/category/date range.

    Filtering here (rather than only in the UI) means future features
    like monthly summaries or search can reuse this without duplicating logic.
    """
    transactions = load_transactions()
    if type_:
        transactions = [t for t in transactions if t.type == type_]
    if category:
        transactions = [t for t in transactions if t.category.lower() == category.lower()]
    if start_date:
        transactions = [t for t in transactions if t.date >= start_date]
    if end_date:
        transactions = [t for t in transactions if t.date <= end_date]
    return transactions


def calculate_total(transactions: list[Transaction], type_: str) -> float:
    """Sum amounts for a given type within an arbitrary (already filtered) list."""
    return sum(t.amount for t in transactions if t.type == type_)


def total_income(transactions: Optional[list[Transaction]] = None) -> float:
    transactions = transactions if transactions is not None else load_transactions()
    return calculate_total(transactions, "income")


def total_expenses(transactions: Optional[list[Transaction]] = None) -> float:
    transactions = transactions if transactions is not None else load_transactions()
    return calculate_total(transactions, "expense")


def balance(transactions: Optional[list[Transaction]] = None) -> float:
    transactions = transactions if transactions is not None else load_transactions()
    return total_income(transactions) - total_expenses(transactions)


def _generate_id(existing_ids: set) -> str:
    """Generate a short unique id not already in use."""
    new_id = uuid.uuid4().hex[:8]
    while new_id in existing_ids:
        new_id = uuid.uuid4().hex[:8]
    return new_id
