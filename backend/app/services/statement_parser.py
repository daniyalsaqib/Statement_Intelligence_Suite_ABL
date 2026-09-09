import csv
import io
import re
from datetime import date, datetime
from typing import Optional

from backend.app.models.statement import StatementLine

CANONICAL_COLUMNS = ("date", "description", "debit", "credit", "balance")

# Normalized alias keys: lowercase, underscores as spaces, collapsed whitespace.
HEADER_ALIASES: dict[str, set[str]] = {
    "date": {
        "date",
        "transaction date",
        "txn date",
    },
    "description": {
        "description",
        "transaction description",
        "details",
        "narration",
        "particulars",
        "merchant",
    },
    "debit": {
        "debit",
        "debit amount",
        "withdrawal",
        "withdrawals",
        "amount debited",
    },
    "credit": {
        "credit",
        "credit amount",
        "deposit",
        "deposits",
        "amount credited",
    },
    "balance": {
        "balance",
        "running balance",
        "closing balance",
    },
}

_CURRENCY_PREFIX_RE = re.compile(
    r"^(?:Rs\.?|PKR|₨|\$)\s*",
    re.IGNORECASE,
)
# Strip trailing currency annotations on headers, e.g. "Debit (Rs)" -> "debit".
_CURRENCY_HEADER_SUFFIX_RE = re.compile(
    r"\s*\((?:rs\.?|pkr|usd|eur|gbp|\$|₨)\)\s*$",
    re.IGNORECASE,
)
_PLAIN_NUMBER_RE = re.compile(r"^-?\d+(?:\.\d+)?$")
_ISO_DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
_NUMERIC_DATE_RE = re.compile(r"^(\d{1,2})([/-])(\d{1,2})\2(\d{4})$")

_MONTH_NAME_FORMATS = (
    "%d-%b-%Y",
    "%d %b %Y",
    "%d-%B-%Y",
    "%d %B %Y",
)


class StatementParseError(ValueError):
    """User-friendly CSV parse/validation error."""


def _normalize_header(name: str) -> str:
    cleaned = name.replace("\ufeff", "").strip().lower().replace("_", " ")
    cleaned = " ".join(cleaned.split())
    cleaned = _CURRENCY_HEADER_SUFFIX_RE.sub("", cleaned).strip()
    return " ".join(cleaned.split())


def _alias_lookup() -> dict[str, str]:
    lookup: dict[str, str] = {}
    for canonical, aliases in HEADER_ALIASES.items():
        for alias in aliases:
            lookup[_normalize_header(alias)] = canonical
    return lookup


_ALIAS_TO_CANONICAL = _alias_lookup()


def _detect_delimiter(text: str) -> str:
    sample = text[:4096]
    if not sample.strip():
        return ","

    try:
        dialect = csv.Sniffer().sniff(sample, delimiters=",;\t")
        if dialect.delimiter in {",", ";", "\t"}:
            return dialect.delimiter
    except csv.Error:
        pass

    first_line = sample.splitlines()[0] if sample.splitlines() else ""
    counts = {
        ",": first_line.count(","),
        ";": first_line.count(";"),
        "\t": first_line.count("\t"),
    }
    best = max(counts, key=counts.get)
    return best if counts[best] > 0 else ","


def _map_headers(fieldnames: Optional[list[Optional[str]]]) -> dict[str, str]:
    if not fieldnames:
        raise StatementParseError(
            "Missing required CSV columns: date, description, debit, credit, balance.\n"
            "Expected columns include: date, description, debit, credit, balance."
        )

    # canonical -> original CSV header key used by DictReader
    mapping: dict[str, str] = {}
    for original in fieldnames:
        if original is None:
            continue
        normalized = _normalize_header(original)
        canonical = _ALIAS_TO_CANONICAL.get(normalized)
        if canonical is None:
            continue
        # First matching header wins if duplicates appear
        mapping.setdefault(canonical, original)

    missing = [col for col in CANONICAL_COLUMNS if col not in mapping]
    if missing:
        label = "column" if len(missing) == 1 else "columns"
        raise StatementParseError(
            f"Missing required CSV {label}: {', '.join(missing)}.\n"
            "Expected columns include: date, description, debit, credit, balance."
        )

    return mapping


def _cell(row: dict, field_map: dict[str, str], canonical: str) -> str:
    raw = row.get(field_map[canonical])
    if raw is None:
        return ""
    return str(raw)


def _is_blank_row(row: dict, field_map: dict[str, str]) -> bool:
    return all(not _cell(row, field_map, col).strip() for col in CANONICAL_COLUMNS)


def _parse_amount(raw: str, field: str, row_num: int, *, required: bool) -> Optional[float]:
    value = raw.strip()
    if not value:
        if required:
            raise StatementParseError(
                f'Row {row_num}: invalid {field} amount "{raw}"'
                if raw != ""
                else f"Row {row_num}: missing {field} amount"
            )
        return None

    display = value
    negative = False
    if value.startswith("(") and value.endswith(")"):
        negative = True
        value = value[1:-1].strip()

    value = _CURRENCY_PREFIX_RE.sub("", value).strip()
    value = value.replace(",", "").strip()

    if not _PLAIN_NUMBER_RE.fullmatch(value):
        raise StatementParseError(f'Row {row_num}: invalid {field} amount "{display}"')

    number = float(value)
    if negative:
        number = -abs(number)
    return number


def _parse_date(raw: str, row_num: int) -> date:
    value = raw.strip()
    if not value:
        raise StatementParseError(f"Row {row_num}: missing date")

    if _ISO_DATE_RE.fullmatch(value):
        try:
            return date.fromisoformat(value)
        except ValueError as exc:
            raise StatementParseError(f'Row {row_num}: invalid date "{raw}"') from exc

    for fmt in _MONTH_NAME_FORMATS:
        try:
            return datetime.strptime(value, fmt).date()
        except ValueError:
            continue

    numeric = _NUMERIC_DATE_RE.fullmatch(value)
    if numeric:
        first = int(numeric.group(1))
        second = int(numeric.group(3))
        year = int(numeric.group(4))

        candidates: list[date] = []
        # DD/MM/YYYY or DD-MM-YYYY
        try:
            candidates.append(date(year, second, first))
        except ValueError:
            pass
        # MM/DD/YYYY (only kept when unambiguous vs DD/MM)
        try:
            candidates.append(date(year, first, second))
        except ValueError:
            pass

        unique: list[date] = []
        seen: set[int] = set()
        for candidate in candidates:
            key = candidate.toordinal()
            if key not in seen:
                seen.add(key)
                unique.append(candidate)

        if len(unique) == 1:
            return unique[0]
        if len(unique) > 1:
            raise StatementParseError(
                f'Row {row_num}: ambiguous date "{raw}". '
                "Use YYYY-MM-DD or an unambiguous day/month format."
            )
        raise StatementParseError(f'Row {row_num}: invalid date "{raw}"')

    raise StatementParseError(
        f'Row {row_num}: invalid date "{raw}". '
        "Supported formats include YYYY-MM-DD, DD/MM/YYYY, DD-MM-YYYY, DD-Mon-YYYY."
    )


def parse_statement_csv(file_content: bytes) -> list[StatementLine]:
    try:
        text = file_content.decode("utf-8-sig")
    except UnicodeDecodeError as exc:
        raise StatementParseError(
            "Could not decode CSV as UTF-8. Please save the file as UTF-8 CSV."
        ) from exc

    delimiter = _detect_delimiter(text)
    reader = csv.DictReader(io.StringIO(text), delimiter=delimiter)
    field_map = _map_headers(reader.fieldnames)

    transactions: list[StatementLine] = []

    for row_num, row in enumerate(reader, start=2):
        if _is_blank_row(row, field_map):
            continue

        date_value = _parse_date(_cell(row, field_map, "date"), row_num)
        description = _cell(row, field_map, "description").strip()
        debit = _parse_amount(
            _cell(row, field_map, "debit"), "debit", row_num, required=False
        )
        credit = _parse_amount(
            _cell(row, field_map, "credit"), "credit", row_num, required=False
        )
        balance = _parse_amount(
            _cell(row, field_map, "balance"), "balance", row_num, required=True
        )
        if balance is None:
            raise StatementParseError(f"Row {row_num}: missing balance amount")

        transactions.append(
            StatementLine(
                date=date_value,
                description=description,
                debit=debit,
                credit=credit,
                balance=balance,
            )
        )

    return transactions
