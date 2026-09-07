"""Minimal CLI test flow for the Day 1 data layer.

Not meant to be pretty -- just enough to prove add/view/delete/totals
work before the real desktop UI gets built on top of data_manager.py.
"""

from models import ValidationError
import data_manager as dm


def print_transaction(t):
    sign = "+" if t.type == "income" else "-"
    note = f"  {t.note}" if t.note else ""
    print(f"[{t.id}] {t.date}  {t.type:<7} {sign}{t.amount:.2f}  {t.category}{note}")


def add_income():
    amount = input("Amount: ")
    category = input("Category: ")
    date = input("Date (YYYY-MM-DD): ")
    note = input("Note (optional): ")
    try:
        t = dm.add_transaction("income", amount, category, date, note)
        print(f"Added income {t.id}")
    except ValidationError as e:
        print(f"Invalid input: {e}")


def add_expense():
    amount = input("Amount: ")
    category = input("Category: ")
    date = input("Date (YYYY-MM-DD): ")
    note = input("Note (optional): ")
    try:
        t = dm.add_transaction("expense", amount, category, date, note)
        print(f"Added expense {t.id}")
    except ValidationError as e:
        print(f"Invalid input: {e}")


def view_transactions():
    transactions = dm.get_transactions()
    if not transactions:
        print("No transactions yet.")
        return
    for t in transactions:
        print_transaction(t)


def delete_transaction_flow():
    transaction_id = input("Transaction id to delete: ").strip()
    if dm.delete_transaction(transaction_id):
        print("Deleted.")
    else:
        print("No transaction with that id.")


def show_total_income():
    print(f"Total income: {dm.total_income():.2f}")


def show_total_expenses():
    print(f"Total expenses: {dm.total_expenses():.2f}")


def show_balance():
    print(f"Balance: {dm.balance():.2f}")


MENU = {
    "1": ("Add income", add_income),
    "2": ("Add expense", add_expense),
    "3": ("View transactions", view_transactions),
    "4": ("Delete a transaction", delete_transaction_flow),
    "5": ("Show total income", show_total_income),
    "6": ("Show total expenses", show_total_expenses),
    "7": ("Show balance", show_balance),
    "8": ("Exit", None),
}


def main():
    while True:
        print("\nExpense Tracker")
        for key, (label, _) in MENU.items():
            print(f"  {key}. {label}")
        choice = input("Choose an option: ").strip()

        if choice == "8":
            print("Bye.")
            break
        entry = MENU.get(choice)
        if entry is None:
            print("Invalid option.")
            continue
        entry[1]()


if __name__ == "__main__":
    main()
