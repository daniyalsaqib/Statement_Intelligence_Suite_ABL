from fastapi import APIRouter, UploadFile, File, HTTPException

from backend.app.services.statement_parser import parse_statement_csv
from backend.app.services.statement_analysis import analyze_statement
from backend.app.services.subscription_analysis import detect_recurring_payments


router = APIRouter(
    prefix="/statement",
    tags=["Statement"],
)


@router.post("/upload")
async def upload_statement(file: UploadFile = File(...)):
    # Only CSV statements are supported for now
    if not file.filename.lower().endswith(".csv"):
        raise HTTPException(
            status_code=400,
            detail="Only CSV files are currently supported.",
        )

    # Read uploaded CSV file
    content = await file.read()

    try:
        # Convert CSV rows into StatementLine objects
        transactions = parse_statement_csv(content)

        # Calculate basic statement summary
        analysis = analyze_statement(transactions)

    except Exception as e:
        raise HTTPException(
            status_code=400,
            detail=f"Could not parse statement: {str(e)}",
        )

    return {
        "filename": file.filename,
        "transaction_count": len(transactions),
        "transactions": transactions,
        "analysis": analysis,
    }


@router.post("/subscriptions")
async def analyze_subscriptions(file: UploadFile = File(...)):
    # Only CSV statements are supported for now
    if not file.filename.lower().endswith(".csv"):
        raise HTTPException(
            status_code=400,
            detail="Only CSV files are currently supported.",
        )

    # Read uploaded CSV file
    content = await file.read()

    try:
        # Convert CSV rows into StatementLine objects
        transactions = parse_statement_csv(content)

        # Detect repeated outgoing payments
        recurring_payments = detect_recurring_payments(transactions)

    except Exception as e:
        raise HTTPException(
            status_code=400,
            detail=f"Could not analyze statement: {str(e)}",
        )

    return {
        "filename": file.filename,
        "recurring_payment_count": len(recurring_payments),
        "recurring_payments": recurring_payments,
    }