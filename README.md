# Expense Tracker

A desktop expense/income tracker, built incrementally. This is a portfolio
project.

## Current functionality (Day 3)

**Data layer (Day 1, extended today):**
- `Transaction` model (id, type, amount, category, date, note).
- CSV-backed storage in `storage/transactions.csv`, created automatically
  on first run.
- Full CRUD: add, update, delete, retrieve.
- Validation for amount, type, category, date, with clear errors instead
  of crashes.
- Total income, total expenses, and balance — work on any list of
  transactions.
- New today: `filter_transactions()` (search by category/note/type +
  type/category/date-range filtering, all combinable, on an already-
  loaded list), `get_categories()` (distinct categories present in the
  data), and `current_month_range()`. The GUI's search bar and filters
  are thin wrappers around these -- no filtering logic is duplicated in
  `gui.py`.

**Desktop GUI (Day 2, extended today):**
- Dashboard (Total Income / Total Expenses / Balance), add-transaction
  form, transaction table, delete -- all as before.
- **Search**: a search box above the table matches category, note, or
  type, case-insensitively, and updates the table live as you type.
- **Filters**: Type (All/Income/Expense), Category (All + whatever
  categories actually exist in your data), and Date (All dates / Current
  month / Custom range with From-To fields). All filters combine with
  each other and with search.
- **Clear Filters** button resets search and all filters back to
  showing everything.
- **Sorting**: click a column heading (Date, Amount, Category, Type) to
  sort the table by it; click again to reverse direction. Sorting only
  changes what's displayed, never the underlying CSV order.
- **Editing**: select a row and click "Edit Selected" (or double-click a
  row) to open an edit dialog for Type/Amount/Category/Date/Note. Saving
  goes through the same validation as adding a transaction; an invalid
  edit shows an inline error and leaves the stored data untouched. The
  transaction's ID never changes.
- **Transaction count**: "Showing X of Y transactions" above the table,
  or a friendly "No transactions match your filters." message when a
  search/filter combination matches nothing (no error popups).
- **Dashboard totals reflect the currently filtered transactions**, with
  a small note under the dashboard clarifying whether you're looking at
  all transactions or a filtered subset.
- The Day 1 CLI still exists in `cli.py` for quick terminal testing of
  the data layer.

Nothing beyond this is implemented yet — no charts, no analytics
visualizations, no export, no settings, no authentication or database.

## Project structure

```
expense_tracker/
├── main.py               # entry point -- launches the GUI
├── gui.py                  # desktop interface: dashboard, form, search/filters, sort, edit dialog
├── cli.py                  # Day 1 terminal test flow, kept for quick testing
├── data_manager.py        # CSV storage + CRUD + totals + filtering/search helpers
├── models.py               # Transaction dataclass + validation
├── test_data_manager.py    # Unit tests for data_manager.py
├── storage/
│   └── transactions.csv   # created automatically, not committed to git
├── requirements.txt
├── .gitignore
└── README.md
```

`gui.py` and `cli.py` only talk to `data_manager.py` -- filtering,
searching, and totals all live there, not in the interface code.

## How to run

Requires Python 3.10+ with Tkinter (bundled with most Python installs;
on some Linux distros install it separately, e.g. `sudo apt install
python3-tk`). No pip packages are required.

```bash
cd expense_tracker
python main.py
```

To use the terminal interface instead:

```bash
python cli.py
```

## Run the tests

```bash
cd expense_tracker
python -m unittest test_data_manager.py -v
```

Covers the data layer, including the new search/filter helpers. The GUI
itself was tested manually and with a scripted headless pass covering:
search by category/note, case-insensitivity, no-match state, each
filter individually and combined (e.g. Expense + Food + current month),
clearing filters, sorting by each column both directions (confirming
the stored CSV order never changes), editing an income and an expense
transaction, an invalid edit (confirming it's rejected and doesn't
touch stored data), and confirming edits/deletes persist after
restarting the app.

## Storage approach

Transactions live in `storage/transactions.csv`, one row per transaction.
The whole file is rewritten on every add/update/delete. Unchanged since
Day 1. `storage/transactions.csv` is gitignored since it's user data;
only the folder structure is tracked.

## Known limitations

- Date fields (add, edit, and the custom filter range) are plain
  validated text entries, not a date picker.
- The category filter/list is derived from whatever's already in your
  data plus the starter list in the add form -- there's no separate
  category management screen.
- Sorting and filtering happen in memory over the full CSV, which is
  fine at personal-tracker scale but wouldn't scale to a very large
  dataset.

## What's coming later

- Charts / analytics
- Export functionality
- Settings

The data layer already supports filtered transaction lists and reusable
totals, so these should build on top of `data_manager.py` without
requiring another rewrite.
