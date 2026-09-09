"""Desktop GUI for the expense tracker.

This module only collects input and displays data -- it does not
duplicate any CRUD or calculation logic. Everything goes through
data_manager.py, same as the Day 1 CLI did.
"""

from __future__ import annotations

import tkinter as tk
from datetime import date
from tkinter import ttk, messagebox

import data_manager as dm
from models import ValidationError

CATEGORIES = ["Food", "Transport", "Shopping", "Bills", "Entertainment", "Education", "Health", "Other"]

WINDOW_MIN_SIZE = (780, 600)

INCOME_COLOR = "#1a7f37"
EXPENSE_COLOR = "#c62828"
BALANCE_COLOR = "#1565c0"


class ExpenseTrackerApp:
    def __init__(self, root: tk.Tk):
        self.root = root
        root.title("Expense Tracker")
        root.minsize(*WINDOW_MIN_SIZE)

        self.type_var = tk.StringVar(value="expense")
        self.amount_var = tk.StringVar()
        self.category_var = tk.StringVar()
        self.date_var = tk.StringVar(value=date.today().isoformat())
        self.note_var = tk.StringVar()
        self.status_var = tk.StringVar()

        self.income_var = tk.StringVar()
        self.expenses_var = tk.StringVar()
        self.balance_var = tk.StringVar()

        self._build_header()
        self._build_dashboard()
        self._build_add_form()
        self._build_transaction_list()

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

    def _build_transaction_list(self):
        outer = ttk.LabelFrame(self.root, text="Transactions", padding=12)
        outer.pack(fill="both", expand=True, padx=16, pady=(0, 4))

        columns = ("id", "type", "amount", "category", "date", "note")
        headings = {"id": "ID", "type": "Type", "amount": "Amount", "category": "Category",
                    "date": "Date", "note": "Note"}
        widths = {"id": 90, "type": 70, "amount": 90, "category": 100, "date": 90, "note": 220}

        self.tree = ttk.Treeview(outer, columns=columns, show="headings", height=10)
        for col in columns:
            self.tree.heading(col, text=headings[col])
            self.tree.column(col, width=widths[col], anchor="w")

        scrollbar = ttk.Scrollbar(outer, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        self.tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        self.tree.tag_configure("income", foreground=INCOME_COLOR)
        self.tree.tag_configure("expense", foreground=EXPENSE_COLOR)

        button_bar = ttk.Frame(self.root, padding=(16, 0, 16, 16))
        button_bar.pack(fill="x")
        ttk.Button(button_bar, text="Delete Selected", command=self.on_delete_selected).pack(anchor="w")

    # ---------- data flow ----------

    def refresh(self):
        """Reload from disk and repaint both the table and the dashboard."""
        try:
            transactions = dm.load_transactions()
        except OSError as e:
            messagebox.showerror("Storage error", str(e))
            transactions = []

        for row in self.tree.get_children():
            self.tree.delete(row)
        for t in transactions:
            sign = "+" if t.type == "income" else "-"
            self.tree.insert(
                "", "end", iid=t.id,
                values=(t.id, t.type, f"{sign}{t.amount:.2f}", t.category, t.date, t.note),
                tags=(t.type,),
            )

        self.income_var.set(f"{dm.total_income(transactions):.2f}")
        self.expenses_var.set(f"{dm.total_expenses(transactions):.2f}")
        self.balance_var.set(f"{dm.balance(transactions):.2f}")

    def on_add_transaction(self):
        try:
            dm.add_transaction(
                self.type_var.get(),
                self.amount_var.get(),
                self.category_var.get(),
                self.date_var.get(),
                self.note_var.get(),
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

    def _reset_form(self):
        self.type_var.set("expense")
        self.amount_var.set("")
        self.category_var.set("")
        self.date_var.set(date.today().isoformat())
        self.note_var.set("")

    def _set_status(self, message: str, error: bool):
        self.status_var.set(message)
        self.status_label.configure(foreground=EXPENSE_COLOR if error else INCOME_COLOR)


def launch():
    root = tk.Tk()
    ExpenseTrackerApp(root)
    root.mainloop()


if __name__ == "__main__":
    launch()
