from fastapi import APIRouter, UploadFile, File, HTTPException

from backend.app.services.statement_parser import parse_statement_csv


router = APIRouter(
    prefix="/statement",
    tags=["Statement"],
)


@router.post("/upload")
async def upload_statement(file: UploadFile = File(...)):
    if not file.filename.lower().endswith(".csv"):
        raise HTTPException(
            status_code=400,
            detail="Only CSV files are currently supported.",
        )

    content = await file.read()

    try:
        transactions = parse_statement_csv(content)
    except Exception as e:
        raise HTTPException(
            status_code=400,
            detail=f"Could not parse statement: {str(e)}",
        )

    return {
        "filename": file.filename,
        "transaction_count": len(transactions),
        "transactions": transactions,
    }