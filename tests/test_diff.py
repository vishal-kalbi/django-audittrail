import datetime
import decimal
import uuid

import pytest

from audittrail.diff import (
    MASK_VALUE,
    _serialize,
    _values_equal,
    compute_create_snapshot,
    compute_delete_snapshot,
    compute_diff,
)


class TestSerialize:
    def test_none(self):
        assert _serialize(None) is None

    def test_str(self):
        assert _serialize("hello") == "hello"

    def test_int(self):
        assert _serialize(42) == 42

    def test_float(self):
        assert _serialize(3.14) == 3.14

    def test_bool(self):
        assert _serialize(True) is True

    def test_decimal(self):
        assert _serialize(decimal.Decimal("9.99")) == "9.99"

    def test_datetime(self):
        dt = datetime.datetime(2026, 1, 15, 10, 30, 0)
        assert _serialize(dt) == "2026-01-15T10:30:00"

    def test_date(self):
        d = datetime.date(2026, 1, 15)
        assert _serialize(d) == "2026-01-15"

    def test_uuid(self):
        u = uuid.UUID("12345678-1234-5678-1234-567812345678")
        assert _serialize(u) == "12345678-1234-5678-1234-567812345678"

    def test_list(self):
        assert _serialize([1, 2, 3]) == [1, 2, 3]

    def test_dict(self):
        assert _serialize({"a": 1}) == {"a": 1}


class TestValuesEqual:
    def test_both_none(self):
        assert _values_equal(None, None) is True

    def test_one_none(self):
        assert _values_equal(None, "x") is False
        assert _values_equal("x", None) is False

    def test_same_strings(self):
        assert _values_equal("a", "a") is True

    def test_different_strings(self):
        assert _values_equal("a", "b") is False

    def test_same_ints(self):
        assert _values_equal(1, 1) is True

    def test_different_types_not_equal(self):
        # int 1 vs str "1" — different types, different serialized forms
        assert _values_equal(1, "1") is False


class TestComputeDiff:
    def test_no_changes(self):
        old = {"name": "Alice", "age": 30}
        new = {"name": "Alice", "age": 30}
        assert compute_diff(old, new) == {}

    def test_single_change(self):
        old = {"name": "Alice", "age": 30}
        new = {"name": "Bob", "age": 30}
        result = compute_diff(old, new)
        assert result == {"name": {"old": "Alice", "new": "Bob"}}

    def test_multiple_changes(self):
        old = {"name": "Alice", "age": 30}
        new = {"name": "Bob", "age": 31}
        result = compute_diff(old, new)
        assert len(result) == 2
        assert result["name"] == {"old": "Alice", "new": "Bob"}
        assert result["age"] == {"old": 30, "new": 31}

    def test_masking(self):
        old = {"name": "Alice", "ssn": "123-45-6789"}
        new = {"name": "Alice", "ssn": "987-65-4321"}
        result = compute_diff(old, new, mask_fields={"ssn"})
        assert result == {"ssn": {"old": MASK_VALUE, "new": MASK_VALUE}}

    def test_none_to_value(self):
        old = {"name": None}
        new = {"name": "Alice"}
        result = compute_diff(old, new)
        assert result == {"name": {"old": None, "new": "Alice"}}


class TestCreateSnapshot:
    def test_basic(self):
        state = {"name": "Alice", "age": 30}
        result = compute_create_snapshot(state)
        assert result == {
            "name": {"old": None, "new": "Alice"},
            "age": {"old": None, "new": 30},
        }

    def test_with_masking(self):
        state = {"name": "Alice", "ssn": "123-45-6789"}
        result = compute_create_snapshot(state, mask_fields={"ssn"})
        assert result["ssn"] == {"old": None, "new": MASK_VALUE}
        assert result["name"] == {"old": None, "new": "Alice"}


class TestDeleteSnapshot:
    def test_basic(self):
        state = {"name": "Alice", "age": 30}
        result = compute_delete_snapshot(state)
        assert result == {
            "name": {"old": "Alice", "new": None},
            "age": {"old": 30, "new": None},
        }

    def test_with_masking(self):
        state = {"name": "Alice", "ssn": "123-45-6789"}
        result = compute_delete_snapshot(state, mask_fields={"ssn"})
        assert result["ssn"] == {"old": MASK_VALUE, "new": None}
