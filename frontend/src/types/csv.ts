export interface CsvColumnSummary {
  name: string;
  detected_type: 'numeric' | 'text' | 'date';
  missing_count: number;
  missing_percentage: number;
  unique_count: number;
  sample_values: string[];
  numeric_min?: number | null;
  numeric_max?: number | null;
  numeric_mean?: number | null;
  numeric_std?: number | null;
}

export interface CsvQualityOverview {
  total_rows: number;
  total_columns: number;
  total_missing_values: number;
  missing_rate_percentage: number;
  duplicate_rows_count: number;
  duplicate_rate_percentage: number;
  numeric_columns_count: number;
  text_columns_count: number;
  date_columns_count: number;
  quality_score: number;
}

export interface CsvAnomaly {
  type: string;
  column: string;
  severity: 'low' | 'medium' | 'high';
  description: string;
  affected_rows_count: number;
}

export interface CsvAiFinding {
  category: string;
  title: string;
  insight: string;
  evidence_columns: string[];
  confidence: number;
}

export interface CsvCompanyDetection {
  detected: boolean;
  company_column?: string | null;
  sample_company_names: string[];
}

export interface CsvAnalysisResponse {
  filename: string;
  file_size_bytes: number;
  quality_overview: CsvQualityOverview;
  columns: CsvColumnSummary[];
  anomalies: CsvAnomaly[];
  ai_findings: CsvAiFinding[];
  company_detection: CsvCompanyDetection;
  parsed_sample_rows: Record<string, unknown>[];
}
