"""Desktop GUI for the expense tracker.

This module only collects input, displays data, and applies search/
filter/sort to an already-loaded transaction list -- it does not
duplicate CRUD or calculation logic. All of that still lives in
data_manager.py (see filter_transactions, get_categories,
current_month_range for the Day 3 additions).
"""

from __future__ import annotations

import tkinter as tk
from datetime import date
from tkinter import ttk, messagebox

import data_manager as dm
from models import ValidationError

CATEGORIES = ["Food", "Transport", "Shopping", "Bills", "Entertainment", "Education", "Health", "Other"]

WINDOW_MIN_SIZE = (900, 700)

INCOME_COLOR = "#1a7f37"
EXPENSE_COLOR = "#c62828"
BALANCE_COLOR = "#1565c0"
MUTED_COLOR = "#555555"

TYPE_FILTER_OPTIONS = ["All", "Income", "Expense"]
DATE_FILTER_OPTIONS = ["All dates", "Current month", "Custom range"]

COLUMNS = ("id", "type", "amount", "category", "date", "note")
COLUMN_HEADINGS = {"id": "ID", "type": "Type", "amount": "Amount", "category": "Category",
                    "date": "Date", "note": "Note"}
COLUMN_WIDTHS = {"id": 90, "type": 70, "amount": 90, "category": 100, "date": 90, "note": 220}

# Columns the user can sort by, and how to read a sort key off a Transaction.
# Sorting only ever reorders what's displayed -- the list this operates on
# is always a copy returned by data_manager, never written back to disk.
SORT_KEYS = {
    "date": lambda t: t.date,
    "amount": lambda t: t.amount,
    "category": lambda t: t.category.lower(),
    "type": lambda t: t.type,
}


class ExpenseTrackerApp:
    def __init__(self, root: tk.Tk):
        self.root = root
        root.title("Expense Tracker")
        root.minsize(*WINDOW_MIN_SIZE)

        # add-transaction form state
        self.type_var = tk.StringVar(value="expense")
        self.amount_var = tk.StringVar()
        self.category_var = tk.StringVar()
        self.date_var = tk.StringVar(value=date.today().isoformat())
        self.note_var = tk.StringVar()
        self.status_var = tk.StringVar()

        # dashboard
        self.income_var = tk.StringVar()
        self.expenses_var = tk.StringVar()
        self.balance_var = tk.StringVar()
        self.dashboard_note_var = tk.StringVar()

        # search / filter state
        self.search_var = tk.StringVar()
        self.type_filter_var = tk.StringVar(value="All")
        self.category_filter_var = tk.StringVar(value="All")
        self.date_filter_var = tk.StringVar(value="All dates")
        self.range_from_var = tk.StringVar()
        self.range_to_var = tk.StringVar()
        self.count_var = tk.StringVar()

        self.sort_column = None
        self.sort_reverse = False
        self.all_transactions: list = []
        self.displayed_transactions: list = []

        self._build_header()
        self._build_dashboard()
        self._build_add_form()
        self._build_filter_bar()
        self._build_transaction_list()

        # wire up live filtering after every relevant widget exists
        self.search_var.trace_add("write", lambda *_: self.apply_filters())
        self.type_filter_var.trace_add("write", lambda *_: self.apply_filters())
        self.category_filter_var.trace_add("write", lambda *_: self.apply_filters())
        self.range_from_var.trace_add("write", lambda *_: self.apply_filters())
        self.range_to_var.trace_add("write", lambda *_: self.apply_filters())

        self.refresh()

    # ---------- layout ----------

    def _build_header(self):
        header = ttk.Frame(self.root, padding=(16, 12))
        header.pack(fill="x")
        ttk.Label(header, text="Expense Tracker", font=("Helvetica", 18, "bold")).pack(anchor="w")

    def _build_dashboard(self):
        frame = ttk.Frame(self.root, padding=(16, 4))
        frame.pack(fill="x")

        self._dashboard_card(frame, "Total Income", self.income_var, INCOME_COLOR, 0)
        self._dashboard_card(frame, "Total Expenses", self.expenses_var, EXPENSE_COLOR, 1)
        self._dashboard_card(frame, "Balance", self.balance_var, BALANCE_COLOR, 2)
        for i in range(3):
            frame.columnconfigure(i, weight=1)

        ttk.Label(self.root, textvariable=self.dashboard_note_var, foreground=MUTED_COLOR,
                  padding=(16, 0)).pack(anchor="w")

    def _dashboard_card(self, parent, title, value_var, color, column):
        card = ttk.Frame(parent, relief="groove", padding=12)
        card.grid(row=0, column=column, sticky="nsew", padx=6, pady=6)
        ttk.Label(card, text=title, font=("Helvetica", 10)).pack(anchor="w")
        tk.Label(card, textvariable=value_var, font=("Helvetica", 16, "bold"), fg=color).pack(anchor="w")

    def _build_add_form(self):
        outer = ttk.LabelFrame(self.root, text="Add Transaction", padding=12)
        outer.pack(fill="x", padx=16, pady=8)

        ttk.Label(outer, text="Type").grid(row=0, column=0, sticky="w", padx=4, pady=4)
        ttk.Combobox(outer, textvariable=self.type_var, values=["income", "expense"],
                     state="readonly", width=10).grid(row=1, column=0, sticky="w", padx=4)

        ttk.Label(outer, text="Amount").grid(row=0, column=1, sticky="w", padx=4, pady=4)
        ttk.Entry(outer, textvariable=self.amount_var, width=12).grid(row=1, column=1, sticky="w", padx=4)

        ttk.Label(outer, text="Category").grid(row=0, column=2, sticky="w", padx=4, pady=4)
        ttk.Combobox(outer, textvariable=self.category_var, values=CATEGORIES, width=14).grid(
            row=1, column=2, sticky="w", padx=4)

        ttk.Label(outer, text="Date (YYYY-MM-DD)").grid(row=0, column=3, sticky="w", padx=4, pady=4)
        ttk.Entry(outer, textvariable=self.date_var, width=14).grid(row=1, column=3, sticky="w", padx=4)

        ttk.Label(outer, text="Note").grid(row=0, column=4, sticky="w", padx=4, pady=4)
        ttk.Entry(outer, textvariable=self.note_var, width=24).grid(row=1, column=4, sticky="w", padx=4)

        ttk.Button(outer, text="Add Transaction", command=self.on_add_transaction).grid(
            row=1, column=5, sticky="w", padx=(12, 4))

        self.status_label = ttk.Label(outer, textvariable=self.status_var)
        self.status_label.grid(row=2, column=0, columnspan=6, sticky="w", padx=4, pady=(8, 0))

    def _build_filter_bar(self):
        outer = ttk.LabelFrame(self.root, text="Search & Filters", padding=12)
        outer.pack(fill="x", padx=16, pady=(0, 8))

        ttk.Label(outer, text="Search (category or note)").grid(row=0, column=0, sticky="w", padx=4, pady=4)
        ttk.Entry(outer, textvariable=self.search_var, width=24).grid(row=1, column=0, sticky="w", padx=4)

        ttk.Label(outer, text="Type").grid(row=0, column=1, sticky="w", padx=4, pady=4)
        ttk.Combobox(outer, textvariable=self.type_filter_var, values=TYPE_FILTER_OPTIONS,
                     state="readonly", width=10).grid(row=1, column=1, sticky="w", padx=4)

        ttk.Label(outer, text="Category").grid(row=0, column=2, sticky="w", padx=4, pady=4)
        self.category_filter_box = ttk.Combobox(outer, textvariable=self.category_filter_var,
                                                  values=["All"], state="readonly", width=14)
        self.category_filter_box.grid(row=1, column=2, sticky="w", padx=4)

        ttk.Label(outer, text="Date").grid(row=0, column=3, sticky="w", padx=4, pady=4)
        date_box = ttk.Combobox(outer, textvariable=self.date_filter_var, values=DATE_FILTER_OPTIONS,
                                 state="readonly", width=13)
        date_box.grid(row=1, column=3, sticky="w", padx=4)
        date_box.bind("<<ComboboxSelected>>", lambda e: self._on_date_filter_changed())

        self.range_from_label = ttk.Label(outer, text="From (YYYY-MM-DD)")
        self.range_from_entry = ttk.Entry(outer, textvariable=self.range_from_var, width=12)
        self.range_to_label = ttk.Label(outer, text="To (YYYY-MM-DD)")
        self.range_to_entry = ttk.Entry(outer, textvariable=self.range_to_var, width=12)
        self.range_from_label.grid(row=0, column=4, sticky="w", padx=4, pady=4)
        self.range_from_entry.grid(row=1, column=4, sticky="w", padx=4)
        self.range_to_label.grid(row=0, column=5, sticky="w", padx=4, pady=4)
        self.range_to_entry.grid(row=1, column=5, sticky="w", padx=4)
        self._set_range_fields_visible(False)

        ttk.Button(outer, text="Clear Filters", command=self.on_clear_filters).grid(
            row=1, column=6, sticky="w", padx=(16, 4))

    def _set_range_fields_visible(self, visible: bool):
        method = "grid" if visible else "grid_remove"
        for widget in (self.range_from_label, self.range_from_entry, self.range_to_label, self.range_to_entry):
            getattr(widget, method)()

    def _on_date_filter_changed(self):
        self._set_range_fields_visible(self.date_filter_var.get() == "Custom range")
        self.apply_filters()

    def _build_transaction_list(self):
        outer = ttk.LabelFrame(self.root, text="Transactions", padding=12)
        outer.pack(fill="both", expand=True, padx=16, pady=(0, 4))

        self.count_label = ttk.Label(outer, textvariable=self.count_var)
        self.count_label.pack(anchor="w", pady=(0, 6))

        table_frame = ttk.Frame(outer)
        table_frame.pack(fill="both", expand=True)

        self.tree = ttk.Treeview(table_frame, columns=COLUMNS, show="headings", height=10, selectmode="browse")
        for col in COLUMNS:
            if col in SORT_KEYS:
                self.tree.heading(col, text=COLUMN_HEADINGS[col], command=lambda c=col: self.on_sort(c))
            else:
                self.tree.heading(col, text=COLUMN_HEADINGS[col])
            self.tree.column(col, width=COLUMN_WIDTHS[col], anchor="w")

        y_scroll = ttk.Scrollbar(table_frame, orient="vertical", command=self.tree.yview)
        x_scroll = ttk.Scrollbar(table_frame, orient="horizontal", command=self.tree.xview)
        self.tree.configure(yscrollcommand=y_scroll.set, xscrollcommand=x_scroll.set)

        self.tree.grid(row=0, column=0, sticky="nsew")
        y_scroll.grid(row=0, column=1, sticky="ns")
        x_scroll.grid(row=1, column=0, sticky="ew")
        table_frame.rowconfigure(0, weight=1)
        table_frame.columnconfigure(0, weight=1)

        self.tree.tag_configure("income", foreground=INCOME_COLOR)
        self.tree.tag_configure("expense", foreground=EXPENSE_COLOR)
        self.tree.bind("<Double-1>", lambda e: self.on_edit_selected())

        button_bar = ttk.Frame(self.root, padding=(16, 0, 16, 16))
        button_bar.pack(fill="x")
        ttk.Button(button_bar, text="Edit Selected", command=self.on_edit_selected).pack(side="left")
        ttk.Button(button_bar, text="Delete Selected", command=self.on_delete_selected).pack(side="left", padx=(8, 0))

    # ---------- data flow ----------

    def refresh(self):
        """Reload everything from disk, then reapply the current search/filter/sort."""
        try:
            self.all_transactions = dm.load_transactions()
        except OSError as e:
            messagebox.showerror("Storage error", str(e))
            self.all_transactions = []
        self._refresh_category_filter_options()
        self.apply_filters()

    def _refresh_category_filter_options(self):
        values = ["All"] + dm.get_categories(self.all_transactions)
        self.category_filter_box["values"] = values
        if self.category_filter_var.get() not in values:
            self.category_filter_var.set("All")

    def apply_filters(self):
        """Filter + sort the in-memory transaction list and repaint the table/dashboard.

        Never touches disk and never mutates self.all_transactions -- this
        only changes what's displayed.
        """
        type_ = None if self.type_filter_var.get() == "All" else self.type_filter_var.get().lower()
        category = None if self.category_filter_var.get() == "All" else self.category_filter_var.get()
        start_date, end_date = self._resolve_date_range()

        filtered = dm.filter_transactions(
            self.all_transactions, type_=type_, category=category,
            start_date=start_date, end_date=end_date, query=self.search_var.get(),
        )

        if self.sort_column:
            filtered = sorted(filtered, key=SORT_KEYS[self.sort_column], reverse=self.sort_reverse)

        self.displayed_transactions = filtered
        self._render_table(filtered)
        self._update_dashboard(filtered)
        self._update_count(filtered)
        self._update_column_headings()

    def _resolve_date_range(self):
        choice = self.date_filter_var.get()
        if choice == "Current month":
            return dm.current_month_range()
        if choice == "Custom range":
            return self.range_from_var.get().strip() or None, self.range_to_var.get().strip() or None
        return None, None

    def _render_table(self, transactions):
        for row in self.tree.get_children():
            self.tree.delete(row)
        for t in transactions:
            sign = "+" if t.type == "income" else "-"
            self.tree.insert(
                "", "end", iid=t.id,
                values=(t.id, t.type, f"{sign}{t.amount:.2f}", t.category, t.date, t.note),
                tags=(t.type,),
            )

    def _update_dashboard(self, transactions):
        self.income_var.set(f"{dm.total_income(transactions):.2f}")
        self.expenses_var.set(f"{dm.total_expenses(transactions):.2f}")
        self.balance_var.set(f"{dm.balance(transactions):.2f}")
        if self._filters_active():
            self.dashboard_note_var.set("Totals reflect the currently filtered transactions.")
        else:
            self.dashboard_note_var.set("Totals reflect all transactions.")

    def _filters_active(self) -> bool:
        return bool(
            self.search_var.get().strip()
            or self.type_filter_var.get() != "All"
            or self.category_filter_var.get() != "All"
            or self.date_filter_var.get() != "All dates"
        )

    def _update_count(self, transactions):
        total = len(self.all_transactions)
        shown = len(transactions)
        if total and not shown:
            self.count_var.set("No transactions match your filters.")
        else:
            self.count_var.set(f"Showing {shown} of {total} transactions")

    def _update_column_headings(self):
        for col in COLUMNS:
            if col not in SORT_KEYS:
                continue
            label = COLUMN_HEADINGS[col]
            if col == self.sort_column:
                label += " ▼" if self.sort_reverse else " ▲"
            self.tree.heading(col, text=label)

    def on_sort(self, column):
        if self.sort_column == column:
            self.sort_reverse = not self.sort_reverse
        else:
            self.sort_column = column
            self.sort_reverse = False
        self.apply_filters()

    def on_clear_filters(self):
        self.search_var.set("")
        self.type_filter_var.set("All")
        self.category_filter_var.set("All")
        self.date_filter_var.set("All dates")
        self.range_from_var.set("")
        self.range_to_var.set("")
        self._set_range_fields_visible(False)
        self.apply_filters()

    def on_add_transaction(self):
        try:
            dm.add_transaction(
                self.type_var.get(), self.amount_var.get(), self.category_var.get(),
                self.date_var.get(), self.note_var.get(),
            )
        except ValidationError as e:
            self._set_status(str(e), error=True)
            return
        except OSError as e:
            self._set_status(f"Could not save: {e}", error=True)
            return

        self._set_status("Transaction added.", error=False)
        self._reset_form()
        self.refresh()

    def on_delete_selected(self):
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("No selection", "Select a transaction to delete first.")
            return
        transaction_id = selected[0]
        if not messagebox.askyesno("Delete transaction", f"Delete transaction {transaction_id}?"):
            return
        try:
            dm.delete_transaction(transaction_id)
        except OSError as e:
            messagebox.showerror("Storage error", str(e))
            return
        self._set_status("Transaction deleted.", error=False)
        self.refresh()

    def on_edit_selected(self):
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("No selection", "Select a transaction to edit first.")
            return
        transaction_id = selected[0]
        transaction = next((t for t in self.all_transactions if t.id == transaction_id), None)
        if transaction is None:
            messagebox.showerror("Not found", "That transaction no longer exists.")
            self.refresh()
            return
        EditTransactionDialog(self.root, transaction, on_saved=self._on_edit_saved)

    def _on_edit_saved(self):
        self._set_status("Transaction updated.", error=False)
        self.refresh()

    def _reset_form(self):
        self.type_var.set("expense")
        self.amount_var.set("")
        self.category_var.set("")
        self.date_var.set(date.today().isoformat())
        self.note_var.set("")

    def _set_status(self, message: str, error: bool):
        self.status_var.set(message)
        self.status_label.configure(foreground=EXPENSE_COLOR if error else INCOME_COLOR)


class EditTransactionDialog(tk.Toplevel):
    """Modal dialog for editing one existing transaction.

    Reuses data_manager.update_transaction directly, so it goes through
    the same validation as adding a transaction. The transaction's id is
    never touched.
    """

    def __init__(self, parent, transaction, on_saved):
        super().__init__(parent)
        self.title(f"Edit Transaction {transaction.id}")
        self.resizable(False, False)
        self.transient(parent)
        self.grab_set()

        self.transaction_id = transaction.id
        self.on_saved = on_saved

        self.type_var = tk.StringVar(value=transaction.type)
        self.amount_var = tk.StringVar(value=str(transaction.amount))
        self.category_var = tk.StringVar(value=transaction.category)
        self.date_var = tk.StringVar(value=transaction.date)
        self.note_var = tk.StringVar(value=transaction.note)
        self.error_var = tk.StringVar()

        pad = dict(padx=8, pady=6)
        frame = ttk.Frame(self, padding=12)
        frame.pack(fill="both", expand=True)

        ttk.Label(frame, text="Type").grid(row=0, column=0, sticky="w", **pad)
        ttk.Combobox(frame, textvariable=self.type_var, values=["income", "expense"],
                     state="readonly", width=15).grid(row=0, column=1, sticky="w", **pad)

        ttk.Label(frame, text="Amount").grid(row=1, column=0, sticky="w", **pad)
        ttk.Entry(frame, textvariable=self.amount_var, width=18).grid(row=1, column=1, sticky="w", **pad)

        ttk.Label(frame, text="Category").grid(row=2, column=0, sticky="w", **pad)
        ttk.Combobox(frame, textvariable=self.category_var, values=CATEGORIES, width=18).grid(
            row=2, column=1, sticky="w", **pad)

        ttk.Label(frame, text="Date (YYYY-MM-DD)").grid(row=3, column=0, sticky="w", **pad)
        ttk.Entry(frame, textvariable=self.date_var, width=18).grid(row=3, column=1, sticky="w", **pad)

        ttk.Label(frame, text="Note").grid(row=4, column=0, sticky="w", **pad)
        ttk.Entry(frame, textvariable=self.note_var, width=28).grid(row=4, column=1, sticky="w", **pad)

        ttk.Label(frame, textvariable=self.error_var, foreground=EXPENSE_COLOR, wraplength=280).grid(
            row=5, column=0, columnspan=2, sticky="w", padx=8)

        button_bar = ttk.Frame(frame)
        button_bar.grid(row=6, column=0, columnspan=2, sticky="e", pady=(8, 0))
        ttk.Button(button_bar, text="Cancel", command=self.destroy).pack(side="right", padx=(8, 0))
        ttk.Button(button_bar, text="Save", command=self.on_save).pack(side="right")

    def on_save(self):
        try:
            dm.update_transaction(
                self.transaction_id,
                type=self.type_var.get(),
                amount=self.amount_var.get(),
                category=self.category_var.get(),
                date=self.date_var.get(),
                note=self.note_var.get(),
            )
        except ValidationError as e:
            self.error_var.set(str(e))
            return
        except OSError as e:
            self.error_var.set(f"Could not save: {e}")
            return
        self.on_saved()
        self.destroy()


def launch():
    root = tk.Tk()
    ExpenseTrackerApp(root)
    root.mainloop()


if __name__ == "__main__":
    launch()
