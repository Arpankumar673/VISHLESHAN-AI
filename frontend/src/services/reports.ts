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
};
