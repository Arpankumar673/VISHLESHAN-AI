from fastapi import APIRouter, Depends, File, UploadFile
from app.core.errors import ValidationError
from app.core.security import AuthenticatedUser, get_current_user
from app.schemas.common import ApiResponse
from app.schemas.csv import CsvAnalysisResponse
from app.services.csv_service import CsvAnalysisService

router = APIRouter()


@router.post("/analyze", response_model=ApiResponse[CsvAnalysisResponse])
async def analyze_csv(
    file: UploadFile = File(...),
    current_user: AuthenticatedUser = Depends(get_current_user),
):
    """
    Parses and analyzes uploaded CSV datasets for data quality, column types,
    duplicates, missing values, statistical anomalies, and corporate entity fields.
    """
    if not file.filename or not (
        file.filename.endswith(".csv") or file.filename.endswith(".txt")
    ):
        raise ValidationError("Only .csv files are supported.")

    file_bytes = await file.read()
    service = CsvAnalysisService()
    result = service.analyze_csv(file_bytes=file_bytes, filename=file.filename)

    return ApiResponse(data=result)
