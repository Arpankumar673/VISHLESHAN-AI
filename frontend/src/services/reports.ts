import { apiClient } from './api';
import { supabase } from '../lib/supabase';
import type { Report } from '../types';

export const reportService = {
  async getReport(reportId: string): Promise<Report> {
    try {
      return await apiClient.get<Report>(`/reports/${reportId}`);
    } catch {
      const { data, error } = await supabase
        .from('reports')
        .select('*, company:companies(*)')
        .eq('id', reportId)
        .single();

      if (error) throw error;
      return data as Report;
    }
  },

  async getReportByRunId(runId: string): Promise<Report | null> {
    try {
      return await apiClient.get<Report>(`/reports/run/${runId}`);
    } catch {
      const { data, error } = await supabase
        .from('reports')
        .select('*, company:companies(*)')
        .eq('research_run_id', runId)
        .maybeSingle();

      if (error) throw error;
      return data as Report | null;
    }
  },

  async downloadReportCsv(reportId: string): Promise<void> {
    const { data: sessionData } = await supabase.auth.getSession();
    const token = sessionData.session?.access_token;
    const rawApiUrl = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api/v1';
    const baseUrl = rawApiUrl.endsWith('/') ? rawApiUrl.slice(0, -1) : rawApiUrl;

    const res = await fetch(`${baseUrl}/reports/${reportId}/export/csv`, {
      headers: {
        Authorization: token ? `Bearer ${token}` : '',
      },
    });

    if (!res.ok) throw new Error('Failed to export CSV report');
    const blob = await res.blob();
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `vishleshan_report_${reportId}.csv`;
    a.click();
    URL.revokeObjectURL(url);
  },

  async downloadReportJson(reportId: string): Promise<void> {
    const reportData = await this.getReport(reportId);
    const blob = new Blob([JSON.stringify(reportData, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `vishleshan_report_${reportId}.json`;
    a.click();
    URL.revokeObjectURL(url);
  },
};
