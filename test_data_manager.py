"""Tests for the expense tracker data layer.

Redirects data_manager's storage paths to a temp directory per test
so this never touches real transaction data.
"""

import os
import shutil
import tempfile
import unittest

import data_manager as dm
from models import ValidationError


class DataManagerTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.original_storage_dir = dm.STORAGE_DIR
        self.original_csv_path = dm.CSV_PATH
        dm.STORAGE_DIR = self.temp_dir
        dm.CSV_PATH = os.path.join(self.temp_dir, "transactions.csv")

    def tearDown(self):
        dm.STORAGE_DIR = self.original_storage_dir
        dm.CSV_PATH = self.original_csv_path
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_csv_created_automatically(self):
        dm.ensure_storage_exists()
        self.assertTrue(os.path.exists(dm.CSV_PATH))

    def test_add_and_load_transaction(self):
        t = dm.add_transaction("income", 100, "Salary", "2026-01-01", "January pay")
        loaded = dm.load_transactions()
        self.assertEqual(len(loaded), 1)
        self.assertEqual(loaded[0].id, t.id)
        self.assertEqual(loaded[0].amount, 100)

    def test_delete_transaction(self):
        t = dm.add_transaction("expense", 50, "Food", "2026-01-02")
        self.assertTrue(dm.delete_transaction(t.id))
        self.assertEqual(len(dm.load_transactions()), 0)

    def test_delete_missing_transaction_returns_false(self):
        self.assertFalse(dm.delete_transaction("does-not-exist"))

    def test_update_transaction(self):
        t = dm.add_transaction("expense", 20, "Transport", "2026-01-03")
        dm.update_transaction(t.id, amount=25, note="updated")
        updated = dm.load_transactions()[0]
        self.assertEqual(updated.amount, 25)
        self.assertEqual(updated.note, "updated")

    def test_totals_and_balance(self):
        dm.add_transaction("income", 1000, "Salary", "2026-01-01")
        dm.add_transaction("expense", 200, "Rent", "2026-01-02")
        dm.add_transaction("expense", 100, "Food", "2026-01-03")
        self.assertEqual(dm.total_income(), 1000)
        self.assertEqual(dm.total_expenses(), 300)
        self.assertEqual(dm.balance(), 700)

    def test_filtered_totals(self):
        dm.add_transaction("income", 500, "Salary", "2026-01-01")
        dm.add_transaction("expense", 50, "Food", "2026-02-01")
        jan_only = dm.get_transactions(start_date="2026-01-01", end_date="2026-01-31")
        self.assertEqual(dm.total_income(jan_only), 500)
        self.assertEqual(dm.total_expenses(jan_only), 0)

    def test_invalid_amount_raises(self):
        with self.assertRaises(ValidationError):
            dm.add_transaction("income", "not-a-number", "Salary", "2026-01-01")

    def test_negative_amount_raises(self):
        with self.assertRaises(ValidationError):
            dm.add_transaction("income", -5, "Salary", "2026-01-01")

    def test_invalid_type_raises(self):
        with self.assertRaises(ValidationError):
            dm.add_transaction("gains", 5, "Salary", "2026-01-01")

    def test_empty_category_raises(self):
        with self.assertRaises(ValidationError):
            dm.add_transaction("income", 5, "", "2026-01-01")

    def test_invalid_date_raises(self):
        with self.assertRaises(ValidationError):
            dm.add_transaction("income", 5, "Salary", "01-01-2026")

    def test_filter_by_query_matches_category_and_note(self):
        dm.add_transaction("expense", 20, "Food", "2026-01-01", "lunch")
        dm.add_transaction("expense", 15, "Transport", "2026-01-02", "bus fare")
        result = dm.filter_transactions(dm.load_transactions(), query="food")
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0].category, "Food")

    def test_filter_by_query_is_case_insensitive(self):
        dm.add_transaction("expense", 20, "Food", "2026-01-01", "Lunch out")
        result = dm.filter_transactions(dm.load_transactions(), query="LUNCH")
        self.assertEqual(len(result), 1)

    def test_filter_by_query_no_match_returns_empty(self):
        dm.add_transaction("expense", 20, "Food", "2026-01-01", "lunch")
        result = dm.filter_transactions(dm.load_transactions(), query="zzz-nomatch")
        self.assertEqual(result, [])

    def test_filter_combines_type_category_and_date(self):
        dm.add_transaction("expense", 20, "Food", "2026-01-15")
        dm.add_transaction("expense", 30, "Food", "2026-02-15")
        dm.add_transaction("income", 100, "Food", "2026-01-15")
        result = dm.filter_transactions(
            dm.load_transactions(), type_="expense", category="Food",
            start_date="2026-01-01", end_date="2026-01-31",
        )
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0].amount, 20)

    def test_get_categories_returns_sorted_unique(self):
        dm.add_transaction("expense", 10, "Transport", "2026-01-01")
        dm.add_transaction("expense", 10, "Food", "2026-01-01")
        dm.add_transaction("expense", 10, "food", "2026-01-01")
        categories = dm.get_categories(dm.load_transactions())
        self.assertEqual(categories, sorted(categories, key=str.lower))
        self.assertIn("Transport", categories)

    def test_current_month_range_brackets_today(self):
        start, end = dm.current_month_range()
        today = dm.date.today().isoformat()
        self.assertLessEqual(start, today)
        self.assertLessEqual(today, end)


if __name__ == "__main__":
    unittest.main()
