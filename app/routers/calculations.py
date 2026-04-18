"""Calculation routes: BREAD operations scoped to the authenticated user."""
from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.auth.jwt import get_current_user
from app.db.database import get_db
from app.models.calculation import Calculation
from app.models.user import User
from app.operations.factory import CalculationFactory
from app.schemas.calculation import (
    CalculationCreate,
    CalculationRead,
    CalculationUpdate,
)

router = APIRouter(prefix="/calculations", tags=["calculations"])


def _compute(calc_type: str, a: float, b: float) -> float:
    """Delegate arithmetic to the Factory so the same logic drives all routes."""
    return CalculationFactory.create(calc_type, a, b).execute()


def _owned_or_404(
    calc_id: int, db: Session, current_user: User
) -> Calculation:
    """Fetch a calculation owned by the current user, else 404."""
    calc = db.query(Calculation).filter(Calculation.id == calc_id).first()
    if calc is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Calculation not found")
    if calc.user_id != current_user.id:
        # 404 (not 403) hides the existence of other users' records.
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Calculation not found")
    return calc


# ---------- Add ----------
@router.post(
    "",
    response_model=CalculationRead,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new calculation",
)
def create_calculation(
    payload: CalculationCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Calculation:
    try:
        result = _compute(payload.type, payload.a, payload.b)
    except ValueError as exc:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, str(exc))

    calc = Calculation(
        a=payload.a,
        b=payload.b,
        type=payload.type,
        result=result,
        user_id=current_user.id,
    )
    db.add(calc)
    db.commit()
    db.refresh(calc)
    return calc


# ---------- Browse ----------
@router.get(
    "",
    response_model=List[CalculationRead],
    summary="List all calculations owned by the current user",
)
def list_calculations(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> List[Calculation]:
    return (
        db.query(Calculation)
        .filter(Calculation.user_id == current_user.id)
        .order_by(Calculation.id.desc())
        .all()
    )


# ---------- Read ----------
@router.get(
    "/{calc_id}",
    response_model=CalculationRead,
    summary="Retrieve a single calculation by id",
)
def get_calculation(
    calc_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Calculation:
    return _owned_or_404(calc_id, db, current_user)


# ---------- Edit ----------
@router.put(
    "/{calc_id}",
    response_model=CalculationRead,
    summary="Update a calculation (recomputes the result)",
)
def update_calculation(
    calc_id: int,
    payload: CalculationUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Calculation:
    calc = _owned_or_404(calc_id, db, current_user)

    if payload.a is not None:
        calc.a = payload.a
    if payload.b is not None:
        calc.b = payload.b
    if payload.type is not None:
        calc.type = payload.type

    try:
        calc.result = _compute(calc.type, calc.a, calc.b)
    except ValueError as exc:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, str(exc))

    db.commit()
    db.refresh(calc)
    return calc


# ---------- Delete ----------
@router.delete(
    "/{calc_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Permanently delete a calculation",
)
def delete_calculation(
    calc_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> None:
    calc = _owned_or_404(calc_id, db, current_user)
    db.delete(calc)
    db.commit()
    return None
