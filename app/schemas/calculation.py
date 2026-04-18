"""Pydantic schemas for the Calculation resource (Pydantic v2)."""
from datetime import datetime
from typing import Literal, Optional
from pydantic import BaseModel, ConfigDict, Field, model_validator

CalcType = Literal["Add", "Sub", "Multiply", "Divide"]


class CalculationCreate(BaseModel):
    """Payload for creating a new calculation.

    `user_id` is intentionally *not* on this schema — it's derived from the
    authenticated JWT so users can only create calculations for themselves.
    """

    a: float = Field(..., description="First operand")
    b: float = Field(..., description="Second operand")
    type: CalcType

    @model_validator(mode="after")
    def check_divide_by_zero(self):
        if self.type == "Divide" and self.b == 0:
            raise ValueError("Cannot divide by zero")
        return self


class CalculationUpdate(BaseModel):
    """Partial-update payload for PUT /calculations/{id}."""

    a: Optional[float] = None
    b: Optional[float] = None
    type: Optional[CalcType] = None

    @model_validator(mode="after")
    def check_divide_by_zero(self):
        if self.type == "Divide" and self.b == 0:
            raise ValueError("Cannot divide by zero")
        return self


class CalculationRead(BaseModel):
    """Public-facing calculation representation."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    a: float
    b: float
    type: str
    result: Optional[float]
    user_id: int
    created_at: datetime
