"""Unit tests for CalculationCreate / CalculationUpdate / CalculationRead schemas."""
from datetime import datetime

import pytest
from pydantic import ValidationError

from app.schemas.calculation import (
    CalculationCreate,
    CalculationRead,
    CalculationUpdate,
)


# ---------- CalculationCreate ----------

def test_valid_create():
    payload = CalculationCreate(a=2, b=3, type="Add")
    assert payload.type == "Add"
    assert payload.a == 2
    assert payload.b == 3


def test_invalid_type_rejected():
    with pytest.raises(ValidationError):
        CalculationCreate(a=1, b=2, type="Power")


def test_divide_by_zero_rejected():
    with pytest.raises(ValidationError, match="Cannot divide by zero"):
        CalculationCreate(a=10, b=0, type="Divide")


def test_divide_nonzero_ok():
    payload = CalculationCreate(a=10, b=2, type="Divide")
    assert payload.b == 2


def test_missing_field_rejected():
    with pytest.raises(ValidationError):
        CalculationCreate(a=1, type="Add")  # type: ignore[call-arg]


def test_create_schema_has_no_user_id():
    """user_id is derived from the JWT server-side, not accepted from clients."""
    assert "user_id" not in CalculationCreate.model_fields


# ---------- CalculationUpdate ----------

def test_update_all_fields_optional():
    """An empty update is structurally valid (no fields required)."""
    upd = CalculationUpdate()
    assert upd.a is None and upd.b is None and upd.type is None


def test_update_partial_ok():
    upd = CalculationUpdate(type="Multiply")
    assert upd.type == "Multiply"
    assert upd.a is None and upd.b is None


def test_update_divide_by_zero_rejected():
    with pytest.raises(ValidationError, match="Cannot divide by zero"):
        CalculationUpdate(type="Divide", b=0)


def test_update_invalid_type_rejected():
    with pytest.raises(ValidationError):
        CalculationUpdate(type="Power")


# ---------- CalculationRead ----------

def test_read_from_attributes():
    """CalculationRead must serialize from an ORM-like object."""

    class FakeCalc:
        id = 1
        a = 2.0
        b = 3.0
        type = "Add"
        result = 5.0
        user_id = 42
        created_at = datetime(2026, 1, 1, 12, 0, 0)

    read = CalculationRead.model_validate(FakeCalc())
    dumped = read.model_dump()
    assert dumped["id"] == 1
    assert dumped["result"] == 5.0
    assert dumped["user_id"] == 42
