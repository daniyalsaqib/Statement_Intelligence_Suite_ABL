import logging

from fastapi import (
    APIRouter,
    File,
    HTTPException,
    UploadFile,
)

from backend.app.services.statement_analysis import (
    analyze_statement,
)
from backend.app.services.statement_parser import (
    StatementParseError,
    parse_statement_csv,
)
from backend.app.services.subscription_analysis import (
    detect_recurring_payments,
)


logger = logging.getLogger(__name__)


router = APIRouter(
    prefix="/statement",
    tags=["Statement"],
)


MAX_UPLOAD_BYTES = 2 * 1024 * 1024
MAX_STATEMENT_ROWS = 5000

UPLOAD_TOO_LARGE_DETAIL = (
    "Uploaded CSV file is too large."
)

TOO_MANY_TRANSACTIONS_DETAIL = (
    "Uploaded CSV contains too many transactions."
)

STATEMENT_PROCESSING_ERROR_DETAIL = (
    "Could not process the uploaded statement. "
    "Please try again."
)

SUBSCRIPTION_PROCESSING_ERROR_DETAIL = (
    "Could not analyze recurring payments. "
    "Please try again."
)


async def _read_csv_upload(
    file: UploadFile,
) -> bytes:
    """
    Validate the uploaded statement and read only up to the
    configured public upload limit plus one detection byte.
    """
    filename = (
        file.filename
        or ""
    )

    if not filename.lower().endswith(
        ".csv"
    ):
        raise HTTPException(
            status_code=400,
            detail=(
                "Only CSV files are currently "
                "supported."
            ),
        )

    content = await file.read(
        MAX_UPLOAD_BYTES + 1
    )

    if (
        len(content)
        > MAX_UPLOAD_BYTES
    ):
        raise HTTPException(
            status_code=413,
            detail=UPLOAD_TOO_LARGE_DETAIL,
        )

    return content


def _parse_uploaded_statement(
    content: bytes,
):
    try:
        return parse_statement_csv(
            content
        )

    except StatementParseError as exc:
        raise HTTPException(
            status_code=400,
            detail=(
                "Could not parse statement: "
                f"{str(exc)}"
            ),
        ) from exc

    except Exception as exc:
        logger.error(
            "Unexpected statement parser failure: "
            "exception_type=%s",
            type(exc).__name__,
        )

        raise HTTPException(
            status_code=500,
            detail=STATEMENT_PROCESSING_ERROR_DETAIL,
        ) from exc


def _enforce_transaction_limit(
    transactions,
):
    if (
        len(transactions)
        > MAX_STATEMENT_ROWS
    ):
        raise HTTPException(
            status_code=413,
            detail=(
                TOO_MANY_TRANSACTIONS_DETAIL
            ),
        )


@router.post("/upload")
async def upload_statement(
    file: UploadFile = File(...),
):
    content = await _read_csv_upload(
        file
    )

    transactions = (
        _parse_uploaded_statement(
            content
        )
    )

    _enforce_transaction_limit(
        transactions
    )

    try:
        analysis = analyze_statement(
            transactions
        )

    except Exception as exc:
        logger.error(
            "Unexpected statement analysis failure: "
            "exception_type=%s",
            type(exc).__name__,
        )

        raise HTTPException(
            status_code=500,
            detail=STATEMENT_PROCESSING_ERROR_DETAIL,
        ) from exc

    return {
        "filename": file.filename,
        "transaction_count": (
            len(transactions)
        ),
        "transactions": transactions,
        "analysis": analysis,
    }


@router.post("/subscriptions")
async def analyze_subscriptions(
    file: UploadFile = File(...),
):
    content = await _read_csv_upload(
        file
    )

    transactions = (
        _parse_uploaded_statement(
            content
        )
    )

    _enforce_transaction_limit(
        transactions
    )

    try:
        recurring_payments = (
            detect_recurring_payments(
                transactions
            )
        )

    except Exception as exc:
        logger.error(
            "Unexpected recurring-payment "
            "analysis failure: exception_type=%s",
            type(exc).__name__,
        )

        raise HTTPException(
            status_code=500,
            detail=(
                SUBSCRIPTION_PROCESSING_ERROR_DETAIL
            ),
        ) from exc

    return {
        "filename": file.filename,
        "recurring_payment_count": (
            len(recurring_payments)
        ),
        "recurring_payments": (
            recurring_payments
        ),
    }
