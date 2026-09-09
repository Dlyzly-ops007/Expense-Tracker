# Expense Tracker

A desktop expense/income tracker, built incrementally. This is a portfolio
project.

## Current functionality (Day 2)

**Data layer (Day 1, unchanged):**
- `Transaction` model (id, type, amount, category, date, note).
- CSV-backed storage in `storage/transactions.csv`, created automatically
  on first run.
- Full CRUD: add, update, delete, retrieve (with optional filtering by
  type / category / date range).
- Validation for amount, type, category, date, with clear errors instead
  of crashes.
- Total income, total expenses, and balance — work on any list of
  transactions, so filtered views can reuse the same functions.

**Desktop GUI (new today):**
- Tkinter/ttk desktop window with a header, dashboard, add-transaction
  form, and transaction table.
- Dashboard shows Total Income, Total Expenses, and Balance, computed by
  `data_manager.py` (not duplicated in the GUI).
- Add-transaction form: type (income/expense dropdown), amount, category
  (dropdown with common starter categories, editable so you can type a
  new one), date, note. Validates through the existing `models.py`
  validation and shows the error inline instead of crashing. On success
  the form clears and the table/dashboard refresh.
- Transaction table (Treeview) listing id, type, amount, category, date,
  note, colour-coded by type. Loads existing transactions on startup.
- Delete: select a row, confirm, and it's removed via the existing
  `data_manager.delete_transaction`; table and dashboard refresh
  afterward.
- The Day 1 CLI still exists in `cli.py` as a lightweight terminal way to
  poke at the data layer, but it's no longer the primary interface.

Nothing beyond this is implemented yet — no charts, no analytics, no
search/filter UI, no monthly summaries, no export, no settings, no
authentication or database.

## Project structure

```
expense_tracker/
├── main.py               # entry point -- launches the GUI
├── gui.py                  # desktop interface (Tkinter/ttk)
├── cli.py                  # Day 1 terminal test flow, kept for quick testing
├── data_manager.py        # CSV storage + CRUD + totals (unchanged from Day 1)
├── models.py               # Transaction dataclass + validation (unchanged)
├── test_data_manager.py    # Unit tests for data_manager.py
├── storage/
│   └── transactions.csv   # created automatically, not committed to git
├── requirements.txt
├── .gitignore
└── README.md
```

`gui.py` and `cli.py` both only talk to `data_manager.py` -- neither one
contains CRUD or calculation logic itself. That's what let the GUI get
built today without touching the data layer.

## How to run

Requires Python 3.10+ with Tkinter (bundled with most Python installs;
on some Linux distros install it separately, e.g. `sudo apt install
python3-tk`). No pip packages are required.

```bash
cd expense_tracker
python main.py
```

This opens the desktop app. Existing data in `storage/transactions.csv`
loads automatically.

To use the old terminal interface instead:

```bash
python cli.py
```

## Run the tests

```bash
cd expense_tracker
python -m unittest test_data_manager.py -v
```

These cover the data layer only (unchanged from Day 1). The GUI was
tested manually: adding income/expenses, verifying totals and balance,
deleting a transaction, restarting to confirm persistence, and a range
of invalid inputs (empty/non-numeric/negative amount, empty category,
bad date format, deleting with nothing selected).

## Storage approach

Transactions live in `storage/transactions.csv`, one row per transaction.
The whole file is rewritten on every add/update/delete. Unchanged from
Day 1. `storage/transactions.csv` is gitignored since it's user data;
only the folder structure is tracked.

## What's coming later

- Charts / analytics
- Search and filtering in the UI
- Monthly summaries
- Export functionality
- Settings

The data layer already supports filtered transaction lists and reusable
totals, so these should build on top of `data_manager.py` without
requiring another rewrite.
