"""Factory pattern for calculation operations."""
from abc import ABC, abstractmethod


class Calculation(ABC):
    """Abstract base for a calculation operation."""

    def __init__(self, a: float, b: float):
        self.a = a
        self.b = b

    @abstractmethod
    def execute(self) -> float:
        ...


class Add(Calculation):
    def execute(self) -> float:
        return self.a + self.b


class Sub(Calculation):
    def execute(self) -> float:
        return self.a - self.b


class Multiply(Calculation):
    def execute(self) -> float:
        return self.a * self.b


class Divide(Calculation):
    def execute(self) -> float:
        if self.b == 0:
            raise ValueError("Cannot divide by zero")
        return self.a / self.b


class CalculationFactory:
    """Return the right Calculation subclass for a given type string."""

    _registry = {
        "Add": Add,
        "Sub": Sub,
        "Multiply": Multiply,
        "Divide": Divide,
    }

    @classmethod
    def create(cls, calc_type: str, a: float, b: float) -> Calculation:
        if calc_type not in cls._registry:
            raise ValueError(f"Unknown calculation type: {calc_type}")
        return cls._registry[calc_type](a, b)
