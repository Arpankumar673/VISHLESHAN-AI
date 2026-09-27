import { apiClient } from './api';
import { supabase } from '../lib/supabase';
import type { Report } from '../types';

export interface DemoCompanyReportResponse {
  mode: string;
  company: {
    name: string;
    official_website: string;
  };
  report: Report;
  source_status: string;
  generated_at: string;
}

export const reportService = {
  async getReport(reportId: string): Promise<Report> {
    // 1. Check local session storage (instant for live demo runs)
    const cached = sessionStorage.getItem(`demo_report_${reportId}`);
    if (cached) {
      try {
        return JSON.parse(cached) as Report;
      } catch {
        // Fall through
      }
    }

    // 2. Try FastAPI /reports/:reportId
    try {
      return await apiClient.get<Report>(`/reports/${reportId}`);
    } catch {
      // 3. Try FastAPI /demo/reports/:reportId
      try {
        const demoRes = await apiClient.get<Report>(`/demo/reports/${reportId}`);
        if (demoRes) return demoRes;
      } catch {
        // Fall through to Supabase
      }

      // 4. Try Supabase direct lookup
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
    const cached = sessionStorage.getItem(`demo_report_${runId}`);
    if (cached) {
      try {
        return JSON.parse(cached) as Report;
      } catch {
        // Fall through
      }
    }

    try {
      return await apiClient.get<Report>(`/reports/run/${runId}`);
    } catch {
      try {
        const demoRes = await apiClient.get<Report>(`/demo/reports/${runId}`);
        if (demoRes) return demoRes;
      } catch {
        // Fall through
      }

      const { data, error } = await supabase
        .from('reports')
        .select('*, company:companies(*)')
        .eq('research_run_id', runId)
        .maybeSingle();

      if (error) throw error;
      return data as Report | null;
    }
  },

  async generateDemoCompanyReport(
    companyName: string,
    officialUrl?: string
  ): Promise<DemoCompanyReportResponse> {
    const res = await apiClient.post<DemoCompanyReportResponse>(
      '/demo/company-report',
      {
        company_name: companyName,
        official_url: officialUrl || undefined,
      }
    );

    if (res?.report?.id) {
      sessionStorage.setItem(`demo_report_${res.report.id}`, JSON.stringify(res.report));
      if (res.report.research_run_id) {
        sessionStorage.setItem(`demo_report_${res.report.research_run_id}`, JSON.stringify(res.report));
      }
    }

    return res;
  },
};
