# -*- coding: utf-8 -*-
"""Focused tests for the 5 validator fixes in _check_schema and validate_with_db."""

import pytest

from ast_parsers.result import ValidationError, ValidationResult
from ast_parsers.tags import ErrorTag
from ast_parsers.validator import validate, _check_schema


# Schema shared across tests
SCHEMA = {
    "users": {"id": "int", "name": "text", "email": "text"},
    "orders": {"id": "int", "user_id": "int", "amount": "decimal", "status": "text"},
    "products": {"id": "int", "name": "text", "price": "decimal"},
}


# =============================================================================
# Fix 2 & 3: CTE column handling
# =============================================================================


class TestCTEColumnHandling:
    """Tests for CTE-derived and CTE-internal column handling."""

    def test_cte_output_column_not_flagged(self):
        """Unqualified column from CTE output should NOT be flagged as hallucinated."""
        sql = """
        WITH revenue AS (
            SELECT user_id, SUM(amount) AS total_rev
            FROM orders
            GROUP BY user_id
        )
        SELECT total_rev FROM revenue
        """
        result = validate(sql, schema=SCHEMA)
        halluc_cols = [
            e for e in result.errors if e.tag == ErrorTag.HALLUCINATION_COLUMN
        ]
        assert halluc_cols == [], (
            f"CTE-output column 'total_rev' should not be flagged: {halluc_cols}"
        )

    def test_cte_internal_column_not_checked(self):
        """Columns inside CTE definitions should not be schema-checked."""
        # 'computed_field' doesn't exist anywhere but is an alias inside the CTE
        sql = """
        WITH enriched AS (
            SELECT id, name || ' <' || email || '>' AS computed_field
            FROM users
        )
        SELECT computed_field FROM enriched
        """
        result = validate(sql, schema=SCHEMA)
        halluc_cols = [
            e for e in result.errors if e.tag == ErrorTag.HALLUCINATION_COLUMN
        ]
        assert halluc_cols == [], (
            f"CTE-internal computed columns should not be flagged: {halluc_cols}"
        )

    def test_cte_with_base_table_columns_still_checked(self):
        """When query has CTEs plus base table refs, base table columns are still checked."""
        sql = """
        WITH top_users AS (
            SELECT user_id FROM orders GROUP BY user_id
        )
        SELECT nonexistent_col FROM users
        WHERE id IN (SELECT user_id FROM top_users)
        """
        result = validate(sql, schema=SCHEMA)
        halluc_cols = [
            e for e in result.errors if e.tag == ErrorTag.HALLUCINATION_COLUMN
        ]
        assert len(halluc_cols) >= 1, (
            "Hallucinated column 'nonexistent_col' against base table 'users' should be caught"
        )

    def test_nested_cte_columns_not_flagged(self):
        """Nested CTEs referencing each other should not produce false positives."""
        sql = """
        WITH step1 AS (
            SELECT user_id, SUM(amount) AS total
            FROM orders
            GROUP BY user_id
        ),
        step2 AS (
            SELECT total FROM step1 WHERE total > 100
        )
        SELECT total FROM step2
        """
        result = validate(sql, schema=SCHEMA)
        halluc_cols = [
            e for e in result.errors if e.tag == ErrorTag.HALLUCINATION_COLUMN
        ]
        assert halluc_cols == [], (
            f"Nested CTE columns should not be flagged: {halluc_cols}"
        )

    def test_cte_alias_not_flagged_as_missing_table(self):
        """CTE names should not be flagged as missing tables."""
        sql = """
        WITH my_cte AS (SELECT id FROM users)
        SELECT id FROM my_cte
        """
        result = validate(sql, schema=SCHEMA)
        halluc_tables = [
            e for e in result.errors if e.tag == ErrorTag.HALLUCINATION_TABLE
        ]
        assert halluc_tables == [], (
            f"CTE alias 'my_cte' should not be flagged as missing table: {halluc_tables}"
        )


# =============================================================================
# Fix 4: Ambiguous column detection
# =============================================================================


class TestAmbiguousColumnDetection:
    """Tests for ambiguous column detection in _check_schema."""

    def test_ambiguous_column_in_join(self):
        """Unqualified column existing in multiple joined tables should be flagged."""
        # Both 'users' and 'orders' have 'id'
        sql = "SELECT id FROM users JOIN orders ON users.id = orders.user_id"
        result = validate(sql, schema=SCHEMA)
        ambig_errors = [e for e in result.errors if e.tag == ErrorTag.AMBIGUOUS_COLUMN]
        assert len(ambig_errors) >= 1, (
            "Unqualified 'id' in JOIN of users+orders should be flagged as ambiguous"
        )

    def test_qualified_column_not_ambiguous(self):
        """Qualified column reference should NOT be flagged as ambiguous."""
        sql = "SELECT users.id FROM users JOIN orders ON users.id = orders.user_id"
        result = validate(sql, schema=SCHEMA)
        ambig_errors = [e for e in result.errors if e.tag == ErrorTag.AMBIGUOUS_COLUMN]
        assert ambig_errors == [], (
            f"Qualified 'users.id' should not be ambiguous: {ambig_errors}"
        )

    def test_unique_column_not_ambiguous(self):
        """Column existing in only one table should not be flagged."""
        sql = "SELECT email FROM users JOIN orders ON users.id = orders.user_id"
        result = validate(sql, schema=SCHEMA)
        ambig_errors = [e for e in result.errors if e.tag == ErrorTag.AMBIGUOUS_COLUMN]
        assert ambig_errors == [], (
            f"'email' only exists in users, should not be ambiguous: {ambig_errors}"
        )

    def test_ambiguous_name_across_three_tables(self):
        """Column 'name' exists in users and products — flagged when both joined."""
        sql = """
        SELECT name
        FROM users
        JOIN products ON users.id = products.id
        """
        result = validate(sql, schema=SCHEMA)
        ambig_errors = [e for e in result.errors if e.tag == ErrorTag.AMBIGUOUS_COLUMN]
        assert len(ambig_errors) >= 1, (
            "'name' exists in both users and products, should be ambiguous"
        )


# =============================================================================
# Fix 5: Partial column check when some tables are missing
# =============================================================================


class TestPartialColumnCheck:
    """Tests that column checks still run for valid tables when others are missing."""

    def test_missing_table_still_checks_valid_table_columns(self):
        """One hallucinated table shouldn't prevent column checks on valid tables."""
        sql = """
        SELECT nonexistent_col
        FROM users
        JOIN fake_table ON users.id = fake_table.fk
        """
        result = validate(sql, schema=SCHEMA)

        # Should have the missing table error
        table_errors = [
            e for e in result.errors if e.tag == ErrorTag.HALLUCINATION_TABLE
        ]
        assert len(table_errors) >= 1, "fake_table should be flagged as missing"

        # Should ALSO have the column error for nonexistent_col against users
        col_errors = [
            e for e in result.errors if e.tag == ErrorTag.HALLUCINATION_COLUMN
        ]
        assert len(col_errors) >= 1, (
            "nonexistent_col should be flagged even though fake_table is missing"
        )

    def test_missing_table_columns_not_checked(self):
        """Columns qualified to a missing table should be skipped, not double-reported."""
        sql = "SELECT fake_table.some_col FROM users JOIN fake_table ON users.id = fake_table.fk"
        result = validate(sql, schema=SCHEMA)

        # Missing table error should exist
        table_errors = [
            e for e in result.errors if e.tag == ErrorTag.HALLUCINATION_TABLE
        ]
        assert len(table_errors) >= 1

        # Column error for fake_table.some_col should NOT exist (table already flagged)
        col_errors = [
            e
            for e in result.errors
            if e.tag == ErrorTag.HALLUCINATION_COLUMN
            and "fake_table" in (e.context or "")
        ]
        assert col_errors == [], (
            f"Columns on missing table shouldn't be separately flagged: {col_errors}"
        )


# =============================================================================
# Existing behavior preservation
# =============================================================================


class TestExistingBehavior:
    """Verify that existing correct behaviors are preserved after the fixes."""

    def test_valid_simple_query(self):
        result = validate("SELECT id, name FROM users", schema=SCHEMA)
        assert result.valid is True
        assert result.errors == []

    def test_valid_join_query(self):
        sql = "SELECT users.name, orders.amount FROM users JOIN orders ON users.id = orders.user_id"
        result = validate(sql, schema=SCHEMA)
        assert result.valid is True

    def test_hallucinated_table_still_caught(self):
        result = validate("SELECT * FROM nonexistent", schema=SCHEMA)
        assert result.valid is False
        tags = [e.tag for e in result.errors]
        assert ErrorTag.HALLUCINATION_TABLE in tags

    def test_hallucinated_column_still_caught(self):
        result = validate("SELECT address FROM users", schema=SCHEMA)
        assert result.valid is False
        tags = [e.tag for e in result.errors]
        assert ErrorTag.HALLUCINATION_COLUMN in tags

    def test_syntax_error_still_caught(self):
        result = validate("SELECT id, name, FROM users")
        assert result.valid is False
        tags = [e.tag for e in result.errors]
        assert ErrorTag.TRAILING_DELIMITER in tags

    def test_subquery_alias_not_flagged(self):
        sql = "SELECT sub.id FROM (SELECT id FROM users) AS sub"
        result = validate(sql, schema=SCHEMA)
        table_errors = [
            e for e in result.errors if e.tag == ErrorTag.HALLUCINATION_TABLE
        ]
        assert table_errors == [], (
            f"Subquery alias 'sub' should not be flagged: {table_errors}"
        )

    def test_syntax_only_no_schema(self):
        result = validate("SELECT * FROM any_table")
        assert result.valid is True
        assert result.errors == []


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
