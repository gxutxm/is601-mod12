"""Unit tests for the CalculationFactory and operation classes."""
import pytest
from app.operations.factory import CalculationFactory


@pytest.mark.parametrize("calc_type,a,b,expected", [
    ("Add", 2, 3, 5),
    ("Sub", 10, 4, 6),
    ("Multiply", 6, 7, 42),
    ("Divide", 20, 5, 4),
])
def test_factory_operations(calc_type, a, b, expected):
    calc = CalculationFactory.create(calc_type, a, b)
    assert calc.execute() == expected


def test_factory_unknown_type():
    with pytest.raises(ValueError, match="Unknown calculation type"):
        CalculationFactory.create("Modulo", 1, 2)


def test_divide_by_zero_raises():
    calc = CalculationFactory.create("Divide", 5, 0)
    with pytest.raises(ValueError, match="Cannot divide by zero"):
        calc.execute()


def test_add_with_floats():
    assert CalculationFactory.create("Add", 1.5, 2.25).execute() == 3.75
