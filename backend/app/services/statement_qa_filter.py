import re
from datetime import date
from typing import Optional

MONTH_NUMBER_TO_NAME = {
    1: "January",
    2: "February",
    3: "March",
    4: "April",
    5: "May",
    6: "June",
    7: "July",
    8: "August",
    9: "September",
    10: "October",
    11: "November",
    12: "December",
}

_MONTH_NAME_TO_NUMBER = {
    "january": 1,
    "jan": 1,
    "february": 2,
    "feb": 2,
    "march": 3,
    "mar": 3,
    "april": 4,
    "apr": 4,
    "may": 5,
    "june": 6,
    "jun": 6,
    "july": 7,
    "jul": 7,
    "august": 8,
    "aug": 8,
    "september": 9,
    "sep": 9,
    "october": 10,
    "oct": 10,
    "november": 11,
    "nov": 11,
    "december": 12,
    "dec": 12,
}

_MONTH_YEAR_RE = re.compile(
    r"\b("
    r"january|february|march|april|june|july|august|september|october|november|december|"
    r"jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec"
    r")\s+(\d{4})\b",
    re.IGNORECASE,
)


def extract_month_year(question: str) -> Optional[tuple[int, int]]:
    """Return (year, month) when the question names a month and a 4-digit year."""
    if not question:
        return None

    match = _MONTH_YEAR_RE.search(question)
    if not match:
        return None

    month = _MONTH_NAME_TO_NUMBER[match.group(1).lower()]
    year = int(match.group(2))
    return year, month


def month_year_label(year: int, month: int) -> str:
    return f"{MONTH_NUMBER_TO_NAME[month]} {year}"


def _parse_iso_date(value: object) -> Optional[date]:
    if not isinstance(value, str):
        return None
    try:
        return date.fromisoformat(value.strip())
    except ValueError:
        return None


def filter_transactions_by_month_year(
    statement_data: list[dict],
    year: int,
    month: int,
) -> list[dict]:
    matching: list[dict] = []
    for row in statement_data:
        if not isinstance(row, dict):
            continue
        parsed = _parse_iso_date(row.get("date"))
        if parsed is None:
            continue
        if parsed.year == year and parsed.month == month:
            matching.append(row)
    return matching
