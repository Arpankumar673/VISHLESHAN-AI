from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class CsvColumnSummary(BaseModel):
    name: str
    detected_type: str
    missing_count: int
    missing_percentage: float
    unique_count: int
    sample_values: List[Any]
    numeric_min: Optional[float] = None
    numeric_max: Optional[float] = None
    numeric_mean: Optional[float] = None
    numeric_std: Optional[float] = None


class CsvQualityOverview(BaseModel):
    total_rows: int
    total_columns: int
    total_missing_values: int
    missing_rate_percentage: float
    duplicate_rows_count: int
    duplicate_rate_percentage: float
    numeric_columns_count: int
    text_columns_count: int
    date_columns_count: int
    quality_score: float  # 0 to 100


class CsvAnomaly(BaseModel):
    type: str
    column: str
    severity: str  # low, medium, high
    description: str
    affected_rows_count: int


class CsvAiFinding(BaseModel):
    category: str
    title: str
    insight: str
    evidence_columns: List[str]
    confidence: float


class CsvCompanyDetection(BaseModel):
    detected: bool
    company_column: Optional[str] = None
    sample_company_names: List[str] = Field(default_factory=list)


class CsvAnalysisResponse(BaseModel):
    filename: str
    file_size_bytes: int
    quality_overview: CsvQualityOverview
    columns: List[CsvColumnSummary]
    anomalies: List[CsvAnomaly]
    ai_findings: List[CsvAiFinding]
    company_detection: CsvCompanyDetection
    parsed_sample_rows: List[Dict[str, Any]]
