from pydantic import BaseModel
from datetime import date
from typing import Optional


class StatementLine(BaseModel):
    date: date
    description: str
    debit: Optional[float] = None
    credit: Optional[float] = None
    balance: float