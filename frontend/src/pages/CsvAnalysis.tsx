import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Upload,
  FileSpreadsheet,
  Search,
  Building2,
  Sparkles,
  BarChart3,
  Download,
} from 'lucide-react';
import { Card, CardContent } from '../components/ui/Card';
import { Button } from '../components/ui/Button';
import { csvService } from '../services/csv';
import { researchService } from '../services/research';
import type { CsvAnalysisResponse } from '../types';

export const CsvAnalysis: React.FC = () => {
  const navigate = useNavigate();
  const [file, setFile] = useState<File | null>(null);
  const [isUploading, setIsUploading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [analysis, setAnalysis] = useState<CsvAnalysisResponse | null>(null);
  const [launchingCompany, setLaunchingCompany] = useState<string | null>(null);

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      const selected = e.target.files[0];
      if (!selected.name.endsWith('.csv') && !selected.name.endsWith('.txt')) {
        setError('Please select a valid .csv file.');
        return;
      }
      setFile(selected);
      setError(null);
    }
  };

  const handleUpload = async () => {
    if (!file) return;
    setIsUploading(true);
    setError(null);
    try {
      const result = await csvService.analyzeCsv(file);
      setAnalysis(result);
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : 'Failed to analyze CSV file.';
      setError(message);
    } finally {
      setIsUploading(false);
    }
  };

  const handleResearchCompany = async (companyName: string) => {
    setLaunchingCompany(companyName);
    try {
      const res = await researchService.startResearch({
        company_name: companyName,
      });
      navigate(`/research/${res.research_run_id}`);
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : 'Failed to launch research run.';
      alert(message);
    } finally {
      setLaunchingCompany(null);
    }
  };

  const handleExportJson = () => {
    if (!analysis) return;
    const blob = new Blob([JSON.stringify(analysis, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `${analysis.filename}_analysis.json`;
    a.click();
    URL.revokeObjectURL(url);
  };

  const handleExportCsvSummary = () => {
    if (!analysis) return;
    let csvContent = 'Column,Detected Type,Missing Count,Missing %,Unique Values,Min,Max,Mean,Std\n';
    analysis.columns.forEach((c) => {
      csvContent += `"${c.name}","${c.detected_type}",${c.missing_count},${c.missing_percentage},${c.unique_count},${c.numeric_min ?? ''},${c.numeric_max ?? ''},${c.numeric_mean ?? ''},${c.numeric_std ?? ''}\n`;
    });
    const blob = new Blob([csvContent], { type: 'text/csv' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `${analysis.filename}_summary.csv`;
    a.click();
    URL.revokeObjectURL(url);
  };

  return (
    <div className="space-y-8 max-w-7xl mx-auto px-4 py-6 sm:px-6 lg:px-8">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-slate-200/80 pb-6">
        <div>
          <div className="flex items-center gap-2 text-sm font-semibold text-[#5b5dfa]">
            <FileSpreadsheet className="h-4 w-4" />
            <span>Dataset Intelligence & Quality Assurance</span>
          </div>
          <h1 className="text-2xl sm:text-3xl font-extrabold text-[#181534] mt-1">
            CSV Data Quality & Entity Analysis
          </h1>
          <p className="text-slate-500 text-sm mt-1">
            Upload CSV datasets for automated schema detection, missingness audit, duplicate checks, statistical anomalies, and corporate entity extraction.
          </p>
        </div>
        {analysis && (
          <div className="flex items-center gap-2">
            <Button variant="secondary" size="sm" onClick={handleExportCsvSummary} leftIcon={<Download className="h-4 w-4" />}>
              Export CSV Summary
            </Button>
            <Button variant="secondary" size="sm" onClick={handleExportJson} leftIcon={<Download className="h-4 w-4" />}>
              Export JSON
            </Button>
          </div>
        )}
      </div>

      {/* Upload Zone */}
      {!analysis && (
        <Card className="border-2 border-dashed border-indigo-200 bg-indigo-50/30 p-8 sm:p-12 text-center rounded-3xl">
          <CardContent className="space-y-6">
            <div className="mx-auto w-16 h-16 rounded-2xl bg-indigo-100 flex items-center justify-center text-[#5b5dfa]">
              <Upload className="h-8 w-8" />
            </div>
            <div>
              <h3 className="text-lg font-bold text-[#181534]">Upload your CSV Dataset</h3>
              <p className="text-sm text-slate-500 max-w-md mx-auto mt-1">
                Drag and drop your dataset file or browse. Maximum file size: 10 MB (up to 50,000 rows).
              </p>
            </div>

            <div className="flex flex-col sm:flex-row items-center justify-center gap-3">
              <label className="cursor-pointer">
                <input
                  type="file"
                  accept=".csv,.txt"
                  className="hidden"
                  onChange={handleFileChange}
                />
                <span className="inline-flex items-center px-6 py-3 rounded-xl bg-white border border-slate-300 font-semibold text-slate-700 shadow-sm hover:bg-slate-50 transition-all">
                  Browse CSV File
                </span>
              </label>
              {file && (
                <Button
                  variant="primary"
                  size="md"
                  onClick={handleUpload}
                  disabled={isUploading}
                  leftIcon={isUploading ? undefined : <BarChart3 className="h-4 w-4" />}
                >
                  {isUploading ? 'Analyzing Dataset...' : 'Start CSV Analysis'}
                </Button>
              )}
            </div>

            {file && (
              <p className="text-xs font-mono text-[#5b5dfa] font-bold">
                Selected File: {file.name} ({(file.size / 1024).toFixed(1)} KB)
              </p>
            )}

            {error && (
              <div className="p-3 bg-red-50 border border-red-200 text-red-700 rounded-xl text-xs font-medium max-w-md mx-auto">
                {error}
              </div>
            )}
          </CardContent>
        </Card>
      )}

      {/* Analysis Results Dashboard */}
      {analysis && (
        <div className="space-y-8">
          {/* File Bar */}
          <div className="flex items-center justify-between p-4 bg-slate-50 rounded-2xl border border-slate-200">
            <div className="flex items-center gap-3">
              <FileSpreadsheet className="h-5 w-5 text-[#5b5dfa]" />
              <div>
                <p className="text-sm font-bold text-[#181534]">{analysis.filename}</p>
                <p className="text-xs text-slate-500">{(analysis.file_size_bytes / 1024).toFixed(1)} KB</p>
              </div>
            </div>
            <Button variant="ghost" size="sm" onClick={() => setAnalysis(null)}>
              Upload New File
            </Button>
          </div>

          {/* Quality Overview Score Cards */}
          <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-4">
            <Card className="p-4 rounded-2xl bg-white border border-slate-200">
              <p className="text-[11px] font-bold text-slate-400 uppercase">Quality Score</p>
              <p className="text-2xl font-extrabold text-[#5b5dfa] mt-1">
                {analysis.quality_overview.quality_score} / 100
              </p>
            </Card>

            <Card className="p-4 rounded-2xl bg-white border border-slate-200">
              <p className="text-[11px] font-bold text-slate-400 uppercase">Total Rows</p>
              <p className="text-2xl font-extrabold text-slate-800 mt-1">
                {analysis.quality_overview.total_rows.toLocaleString()}
              </p>
            </Card>

            <Card className="p-4 rounded-2xl bg-white border border-slate-200">
              <p className="text-[11px] font-bold text-slate-400 uppercase">Total Columns</p>
              <p className="text-2xl font-extrabold text-slate-800 mt-1">
                {analysis.quality_overview.total_columns}
              </p>
            </Card>

            <Card className="p-4 rounded-2xl bg-white border border-slate-200">
              <p className="text-[11px] font-bold text-slate-400 uppercase">Missing Values</p>
              <p className="text-2xl font-extrabold text-amber-600 mt-1">
                {analysis.quality_overview.missing_rate_percentage}%
              </p>
            </Card>

            <Card className="p-4 rounded-2xl bg-white border border-slate-200">
              <p className="text-[11px] font-bold text-slate-400 uppercase">Duplicate Rows</p>
              <p className="text-2xl font-extrabold text-red-600 mt-1">
                {analysis.quality_overview.duplicate_rows_count}
              </p>
            </Card>

            <Card className="p-4 rounded-2xl bg-white border border-slate-200">
              <p className="text-[11px] font-bold text-slate-400 uppercase">Numeric Fields</p>
              <p className="text-2xl font-extrabold text-emerald-600 mt-1">
                {analysis.quality_overview.numeric_columns_count}
              </p>
            </Card>
          </div>

          {/* Vishleshan Entity Linking Banner */}
          {analysis.company_detection.detected && (
            <Card className="border-2 border-indigo-200 bg-indigo-50/50 p-6 rounded-2xl">
              <div className="flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
                <div className="space-y-1">
                  <div className="flex items-center gap-2 text-xs font-bold text-[#5b5dfa]">
                    <Building2 className="h-4 w-4" />
                    <span>Vishleshan AI Corporate Entity Integration</span>
                  </div>
                  <h4 className="text-lg font-bold text-[#181534]">
                    Detected Corporate Field: '{analysis.company_detection.company_column}'
                  </h4>
                  <p className="text-xs text-slate-600">
                    Found {analysis.company_detection.sample_company_names.length} sample organization(s) in this dataset. Select any organization to launch an automated 8-agent Vishleshan research run.
                  </p>
                </div>
              </div>

              <div className="mt-4 flex flex-wrap gap-2.5">
                {analysis.company_detection.sample_company_names.map((comp) => (
                  <Button
                    key={comp}
                    variant="secondary"
                    size="sm"
                    className="bg-white hover:bg-indigo-50 text-[#181534] border-indigo-200"
                    onClick={() => handleResearchCompany(comp)}
                    disabled={launchingCompany === comp}
                    rightIcon={<Search className="h-3 w-3 text-[#5b5dfa]" />}
                  >
                    {launchingCompany === comp ? 'Launching Research...' : `Research '${comp}'`}
                  </Button>
                ))}
              </div>
            </Card>
          )}

          {/* AI Insights & Findings */}
          <div className="space-y-4">
            <h3 className="text-lg font-bold text-[#181534] flex items-center gap-2">
              <Sparkles className="h-5 w-5 text-[#5b5dfa]" />
              <span>Evidence-Grounded AI Findings</span>
            </h3>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {analysis.ai_findings.map((f, i) => (
                <Card key={i} className="p-5 rounded-2xl border border-slate-200">
                  <div className="flex items-start justify-between">
                    <div>
                      <span className="text-[10px] font-extrabold uppercase text-[#5b5dfa]">
                        {f.category}
                      </span>
                      <h4 className="text-sm font-bold text-[#181534] mt-0.5">{f.title}</h4>
                    </div>
                    <span className="text-xs font-mono font-bold text-slate-400">
                      {(f.confidence * 100).toFixed(0)}% conf
                    </span>
                  </div>
                  <p className="text-xs text-slate-600 mt-2 leading-relaxed">{f.insight}</p>
                </Card>
              ))}
            </div>
          </div>

          {/* Column Inspector */}
          <div className="space-y-4">
            <h3 className="text-lg font-bold text-[#181534] flex items-center gap-2">
              <BarChart3 className="h-5 w-5 text-[#5b5dfa]" />
              <span>Column Schema Inspector ({analysis.columns.length} Columns)</span>
            </h3>

            <div className="overflow-x-auto rounded-2xl border border-slate-200 bg-white">
              <table className="w-full text-left border-collapse text-xs">
                <thead>
                  <tr className="bg-slate-50 border-b border-slate-200 text-slate-500 font-bold uppercase text-[10px]">
                    <th className="px-4 py-3">Column Name</th>
                    <th className="px-4 py-3">Type</th>
                    <th className="px-4 py-3">Missing</th>
                    <th className="px-4 py-3">Unique</th>
                    <th className="px-4 py-3">Numeric Stats (Min / Max / Mean)</th>
                    <th className="px-4 py-3">Sample Values</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100">
                  {analysis.columns.map((c) => (
                    <tr key={c.name} className="hover:bg-slate-50/50">
                      <td className="px-4 py-3 font-bold text-[#181534]">{c.name}</td>
                      <td className="px-4 py-3">
                        <span
                          className={`inline-block px-2 py-0.5 rounded text-[10px] font-mono font-bold uppercase ${
                            c.detected_type === 'numeric'
                              ? 'bg-emerald-50 text-emerald-700'
                              : c.detected_type === 'date'
                              ? 'bg-purple-50 text-purple-700'
                              : 'bg-slate-100 text-slate-700'
                          }`}
                        >
                          {c.detected_type}
                        </span>
                      </td>
                      <td className="px-4 py-3 text-slate-600 font-mono">
                        {c.missing_count} ({c.missing_percentage}%)
                      </td>
                      <td className="px-4 py-3 text-slate-600 font-mono">{c.unique_count}</td>
                      <td className="px-4 py-3 font-mono text-slate-600">
                        {c.numeric_min !== undefined && c.numeric_min !== null
                          ? `${c.numeric_min} / ${c.numeric_max} / ${c.numeric_mean}`
                          : '—'}
                      </td>
                      <td className="px-4 py-3 text-slate-500 font-mono max-w-xs truncate">
                        {c.sample_values.join(', ')}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
