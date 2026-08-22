import csv
import io
import math
import statistics
from typing import Any, Dict, List, Optional, Tuple
from app.core.errors import ValidationError
from app.schemas.csv import (
    CsvAiFinding,
    CsvAnalysisResponse,
    CsvAnomaly,
    CsvColumnSummary,
    CsvCompanyDetection,
    CsvQualityOverview,
)

MAX_CSV_FILE_SIZE_BYTES = 10 * 1024 * 1024  # 10 MB
MAX_CSV_ROWS = 50000
MAX_CSV_COLS = 100


class CsvAnalysisService:
    def analyze_csv(self, file_bytes: bytes, filename: str) -> CsvAnalysisResponse:
        if not file_bytes:
            raise ValidationError("CSV file is empty.")

        file_size = len(file_bytes)
        if file_size > MAX_CSV_FILE_SIZE_BYTES:
            raise ValidationError(
                f"File size ({file_size / (1024*1024):.1f} MB) exceeds maximum limit of 10 MB."
            )

        # 1. Decode bytes using UTF-8 or Latin-1
        try:
            content_str = file_bytes.decode("utf-8")
        except UnicodeDecodeError:
            try:
                content_str = file_bytes.decode("latin-1")
            except Exception as exc:
                raise ValidationError(f"Failed to decode CSV encoding: {exc}")

        # 2. Parse using Python built-in csv module
        try:
            reader = csv.reader(io.StringIO(content_str))
            rows = [row for row in reader if any(field.strip() for field in row)]
        except Exception as exc:
            raise ValidationError(f"Invalid or malformed CSV file: {exc}")

        if not rows:
            raise ValidationError("CSV dataset contains no data rows.")

        headers = [str(h).strip() for h in rows[0]]
        data_rows = rows[1:]

        if not data_rows:
            raise ValidationError("CSV dataset contains headers but no data records.")

        if len(data_rows) > MAX_CSV_ROWS:
            data_rows = data_rows[:MAX_CSV_ROWS]
        if len(headers) > MAX_CSV_COLS:
            headers = headers[:MAX_CSV_COLS]
            data_rows = [r[:MAX_CSV_COLS] for r in data_rows]

        total_rows = len(data_rows)
        total_cols = len(headers)
        total_cells = total_rows * total_cols

        # 3. Duplicate row check
        seen_rows = set()
        duplicate_rows_count = 0
        for r in data_rows:
            row_tuple = tuple(r)
            if row_tuple in seen_rows:
                duplicate_rows_count += 1
            else:
                seen_rows.add(row_tuple)

        duplicate_rate = (duplicate_rows_count / total_rows * 100.0) if total_rows > 0 else 0.0

        anomalies: List[CsvAnomaly] = []
        if duplicate_rows_count > 0:
            anomalies.append(
                CsvAnomaly(
                    type="duplicate_rows",
                    column="Dataset",
                    severity="high" if duplicate_rate > 10.0 else "medium",
                    description=f"Identified {duplicate_rows_count} duplicate row(s) ({duplicate_rate:.1f}% of total).",
                    affected_rows_count=duplicate_rows_count,
                )
            )

        # 4. Column Analysis
        column_summaries: List[CsvColumnSummary] = []
        numeric_count = 0
        text_count = 0
        date_count = 0
        total_missing = 0

        company_col_name: Optional[str] = None
        company_samples: List[str] = []

        for col_idx, col_name in enumerate(headers):
            values = [row[col_idx].strip() if col_idx < len(row) else "" for row in data_rows]
            non_empty_values = [v for v in values if v != ""]
            missing_cnt = total_rows - len(non_empty_values)
            total_missing += missing_cnt
            missing_pct = (missing_cnt / total_rows * 100.0) if total_rows > 0 else 0.0

            unique_values = set(non_empty_values)
            unique_cnt = len(unique_values)

            col_lower = col_name.lower().strip()
            if not company_col_name and any(
                k in col_lower
                for k in ["company", "organization", "firm", "employer", "target_entity", "company_name"]
            ):
                company_col_name = col_name
                company_samples = list(dict.fromkeys(non_empty_values))[:10]

            # Try numeric parsing
            numeric_vals: List[float] = []
            for v in non_empty_values:
                try:
                    # Remove common thousands separators or currency symbols
                    clean_v = v.replace(",", "").replace("$", "").replace("€", "").replace("£", "")
                    num = float(clean_v)
                    numeric_vals.append(num)
                except ValueError:
                    pass

            is_numeric = len(numeric_vals) >= 0.8 * len(non_empty_values) if non_empty_values else False

            min_val = None
            max_val = None
            mean_val = None
            std_val = None

            if is_numeric and numeric_vals:
                numeric_count += 1
                det_type = "numeric"
                min_val = min(numeric_vals)
                max_val = max(numeric_vals)
                mean_val = statistics.mean(numeric_vals)
                std_val = statistics.stdev(numeric_vals) if len(numeric_vals) > 1 else 0.0

                # IQR Outlier test
                sorted_vals = sorted(numeric_vals)
                n = len(sorted_vals)
                q1 = sorted_vals[int(n * 0.25)]
                q3 = sorted_vals[int(n * 0.75)]
                iqr = q3 - q1
                if iqr > 0:
                    outliers = [v for v in numeric_vals if v < q1 - 1.5 * iqr or v > q3 + 1.5 * iqr]
                    if outliers:
                        anomalies.append(
                            CsvAnomaly(
                                type="statistical_outlier",
                                column=col_name,
                                severity="medium",
                                description=f"Found {len(outliers)} statistical outlier value(s) in numeric field '{col_name}'.",
                                affected_rows_count=len(outliers),
                            )
                        )
            else:
                # Date keyword check
                if "date" in col_lower or "time" in col_lower or "year" in col_lower:
                    date_count += 1
                    det_type = "date"
                else:
                    text_count += 1
                    det_type = "text"

            if missing_pct > 30.0:
                anomalies.append(
                    CsvAnomaly(
                        type="high_missingness",
                        column=col_name,
                        severity="high" if missing_pct > 50.0 else "medium",
                        description=f"Column '{col_name}' has high missingness ({missing_pct:.1f}% missing).",
                        affected_rows_count=missing_cnt,
                    )
                )

            samples = list(dict.fromkeys(non_empty_values))[:5]
            column_summaries.append(
                CsvColumnSummary(
                    name=col_name,
                    detected_type=det_type,
                    missing_count=missing_cnt,
                    missing_percentage=round(missing_pct, 2),
                    unique_count=unique_cnt,
                    sample_values=samples,
                    numeric_min=round(min_val, 2) if min_val is not None else None,
                    numeric_max=round(max_val, 2) if max_val is not None else None,
                    numeric_mean=round(mean_val, 2) if mean_val is not None else None,
                    numeric_std=round(std_val, 2) if std_val is not None else None,
                )
            )

        missing_rate_pct = (total_missing / total_cells * 100.0) if total_cells > 0 else 0.0

        quality_score = 100.0 - (missing_rate_pct * 0.5) - (duplicate_rate * 0.5) - (len(anomalies) * 2.0)
        quality_score = max(10.0, min(100.0, round(quality_score, 1)))

        overview = CsvQualityOverview(
            total_rows=total_rows,
            total_columns=total_cols,
            total_missing_values=total_missing,
            missing_rate_percentage=round(missing_rate_pct, 2),
            duplicate_rows_count=duplicate_rows_count,
            duplicate_rate_percentage=round(duplicate_rate, 2),
            numeric_columns_count=numeric_count,
            text_columns_count=text_count,
            date_columns_count=date_count,
            quality_score=quality_score,
        )

        ai_findings: List[CsvAiFinding] = [
            CsvAiFinding(
                category="Dataset Quality",
                title=f"Data Quality Index: {quality_score}/100",
                insight=f"Parsed {total_rows} records across {total_cols} columns. Overall data completeness calculated at {(100.0 - missing_rate_pct):.1f}%.",
                evidence_columns=[col.name for col in column_summaries[:3]],
                confidence=0.95,
            )
        ]

        if duplicate_rows_count > 0:
            ai_findings.append(
                CsvAiFinding(
                    category="Redundancy",
                    title=f"Duplicate Rows Detected ({duplicate_rows_count} records)",
                    insight=f"Detected {duplicate_rows_count} duplicate row(s) ({duplicate_rate:.1f}% rate). Deduplication recommended.",
                    evidence_columns=["All Columns"],
                    confidence=0.98,
                )
            )

        if company_col_name:
            ai_findings.append(
                CsvAiFinding(
                    category="Vishleshan AI Entity Linking",
                    title=f"Corporate Entity Column Identified ('{company_col_name}')",
                    insight=f"Identified corporate entity field '{company_col_name}' containing {len(company_samples)} sample organization(s). Enable direct research run from dashboard.",
                    evidence_columns=[company_col_name],
                    confidence=0.92,
                )
            )

        sample_rows_dict: List[Dict[str, Any]] = []
        for r in data_rows[:15]:
            row_dict = {}
            for col_idx, col_name in enumerate(headers):
                val = r[col_idx] if col_idx < len(r) else ""
                row_dict[col_name] = val
            sample_rows_dict.append(row_dict)

        return CsvAnalysisResponse(
            filename=filename,
            file_size_bytes=file_size,
            quality_overview=overview,
            columns=column_summaries,
            anomalies=anomalies,
            ai_findings=ai_findings,
            company_detection=CsvCompanyDetection(
                detected=bool(company_col_name),
                company_column=company_col_name,
                sample_company_names=company_samples,
            ),
            parsed_sample_rows=sample_rows_dict,
        )
