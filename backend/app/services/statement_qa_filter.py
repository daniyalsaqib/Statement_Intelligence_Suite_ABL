import re
from dataclasses import dataclass
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
    "sept": 9,
    "october": 10,
    "oct": 10,
    "november": 11,
    "nov": 11,
    "december": 12,
    "dec": 12,
}

_MONTH_PATTERN = (
    r"january|february|march|april|may|june|july|august|"
    r"september|october|november|december|"
    r"jan|feb|mar|apr|jun|jul|aug|sep|sept|oct|nov|dec"
)

_MONTH_RE = re.compile(
    rf"\b({_MONTH_PATTERN})\b",
    re.IGNORECASE,
)

_MONTH_YEAR_RE = re.compile(
    rf"\b({_MONTH_PATTERN})\s+(\d{{4}})\b",
    re.IGNORECASE,
)

_YEAR_RE = re.compile(r"\b(\d{4})\b")


@dataclass(frozen=True)
class MonthScopeResolution:
    scopes: tuple[tuple[int, int], ...]
    has_month_reference: bool
    error: str | None = None


def _mentioned_month_numbers(
    question: str,
) -> list[int]:
    if not question:
        return []

    months = []

    for match in _MONTH_RE.finditer(question):
        alias = match.group(1).lower()

        # "May" is both a month and an English modal verb.
        #
        # Examples that must NOT be interpreted as a month:
        #
        # May I see my total spending?
        # May we review the statement?
        #
        # Real month references such as "in May" and
        # "May 2026" continue to work.
        if alias == "may" and not question[: match.start()].strip():
            remainder = question[match.end() :]

            if re.match(
                (r"\s+(?:" r"i|we|you|he|she|they|it|be" r")\b"),
                remainder,
                re.IGNORECASE,
            ):
                continue

        month_number = _MONTH_NAME_TO_NUMBER[alias]

        if month_number not in months:
            months.append(month_number)

    return months


def extract_month_years(
    question: str,
) -> list[tuple[int, int]]:
    if not question:
        return []

    months = _mentioned_month_numbers(question)

    years = list(
        dict.fromkeys(int(match.group(1)) for match in _YEAR_RE.finditer(question))
    )

    # One shared year can apply to several named months:
    # "July and August 2026".
    if months and len(years) == 1:
        return [(years[0], month) for month in months]

    # Otherwise retain directly paired month/year references.
    scopes = [
        (
            int(match.group(2)),
            _MONTH_NAME_TO_NUMBER[match.group(1).lower()],
        )
        for match in _MONTH_YEAR_RE.finditer(question)
    ]

    return list(dict.fromkeys(scopes))


def extract_month_year(
    question: str,
) -> Optional[tuple[int, int]]:
    """
    Backward-compatible helper for callers that expect
    one month/year scope.
    """
    scopes = extract_month_years(question)

    return scopes[0] if scopes else None


def month_year_label(
    year: int,
    month: int,
) -> str:
    return f"{MONTH_NUMBER_TO_NAME[month]} " f"{year}"


def _parse_iso_date(
    value: object,
) -> Optional[date]:
    if not isinstance(
        value,
        str,
    ):
        return None

    try:
        return date.fromisoformat(value.strip())

    except ValueError:
        return None


def _years_present_for_month(
    statement_data: list[dict],
    month: int,
) -> list[int]:
    years = set()

    for row in statement_data:
        if not isinstance(
            row,
            dict,
        ):
            continue

        parsed = _parse_iso_date(row.get("date"))

        if parsed is not None and parsed.month == month:
            years.add(parsed.year)

    return sorted(years)


def resolve_month_scopes(
    question: str,
    statement_data: list[dict],
) -> MonthScopeResolution:
    """
    Resolve explicit and month-only statement periods.

    Month-only questions are allowed when the requested month
    exists in exactly one year in the supplied statement.
    """
    months = _mentioned_month_numbers(question)

    if not months:
        return MonthScopeResolution(
            scopes=(),
            has_month_reference=False,
        )

    direct_scopes = extract_month_years(question)

    if direct_scopes:
        return MonthScopeResolution(
            scopes=tuple(direct_scopes),
            has_month_reference=True,
        )

    resolved = []

    for month in months:
        years = _years_present_for_month(
            statement_data,
            month,
        )

        name = MONTH_NUMBER_TO_NAME[month]

        if not years:
            return MonthScopeResolution(
                scopes=(),
                has_month_reference=True,
                error=(f"No transactions found for " f"{name}."),
            )

        if len(years) > 1:
            return MonthScopeResolution(
                scopes=(),
                has_month_reference=True,
                error=(
                    f"Multiple {name} periods were found. "
                    f"Please include the year in your question."
                ),
            )

        resolved.append(
            (
                years[0],
                month,
            )
        )

    return MonthScopeResolution(
        scopes=tuple(dict.fromkeys(resolved)),
        has_month_reference=True,
    )


def filter_transactions_by_month_year(
    statement_data: list[dict],
    year: int,
    month: int,
) -> list[dict]:
    return filter_transactions_by_scopes(
        statement_data,
        [(year, month)],
    )


def filter_transactions_by_scopes(
    statement_data: list[dict],
    scopes: list[tuple[int, int]] | tuple[tuple[int, int], ...],
) -> list[dict]:
    scope_set = set(scopes)

    matching = []

    for row in statement_data:
        if not isinstance(
            row,
            dict,
        ):
            continue

        parsed = _parse_iso_date(row.get("date"))

        if parsed is None:
            continue

        if (
            parsed.year,
            parsed.month,
        ) in scope_set:
            matching.append(row)

    return matching
