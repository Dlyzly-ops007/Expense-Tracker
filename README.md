# Expense Tracker

A desktop expense/income tracker, built incrementally. This is a portfolio
project — Day 1 covers the data layer only.

## Day 1: what's implemented

- A `Transaction` model (id, type, amount, category, date, note).
- CSV-backed storage in `storage/transactions.csv`, created automatically
  on first run.
- Full CRUD: add, update, delete, retrieve (with optional filtering by
  type / category / date range).
- Validation for amount, type, category, date, with clear errors instead
  of crashes.
- Total income, total expenses, and balance calculations — these work on
  any list of transactions, not just "all of them", so filtered views
  (e.g. a future month view) can reuse the same functions.
- A bare-bones CLI (`main.py`) to exercise all of the above.
- Unit tests for the core data operations (`test_data_manager.py`).

Nothing beyond this is implemented yet — no GUI, no charts, no export,
no search UI, no settings.

## Project structure

```
expense_tracker/
├── main.py               # CLI test flow (temporary, until the GUI exists)
├── data_manager.py        # CSV storage + CRUD + totals (the real logic)
├── models.py               # Transaction dataclass + validation
├── test_data_manager.py    # Unit tests for data_manager.py
├── storage/
│   └── transactions.csv   # created automatically, not committed to git
├── requirements.txt
├── .gitignore
└── README.md
```

`main.py` only talks to `data_manager.py`. `data_manager.py` doesn't know
anything about the CLI. That split is what lets the future GUI plug in
without touching the storage/validation logic.

## How to run

Requires Python 3.10+ (standard library only, no install step needed).

```bash
cd expense_tracker
python main.py
```

You'll get a numbered menu to add income/expenses, view all
transactions, delete one, and see totals/balance.

## Run the tests

```bash
cd expense_tracker
python -m unittest test_data_manager.py -v
```

## Storage approach

Transactions live in `storage/transactions.csv`, one row per transaction.
The whole file is rewritten on every add/update/delete — simple and fine
at this scale. `storage/transactions.csv` is gitignored since it's user
data; only the folder structure is tracked.

## What's coming later

- Desktop GUI (replacing `main.py`)
- Charts / analytics
- Search and filtering in the UI
- Monthly summaries
- Export functionality
- Settings

The data layer (`data_manager.py`, `models.py`) is meant to support all of
that without a rewrite — the filtering and totals functions already accept
arbitrary transaction lists for exactly this reason.
