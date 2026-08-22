import { apiClient } from './api';
import { supabase } from '../lib/supabase';
import type {
  ResearchRun,
  StartResearchPayload,
  StartResearchResponse,
} from '../types';

export const researchService = {
  async startResearch(
    payload: StartResearchPayload
  ): Promise<StartResearchResponse> {
    return await apiClient.post<StartResearchResponse>('/research', payload);
  },

  async getResearchRun(runId: string): Promise<ResearchRun> {
    try {
      const res = await apiClient.get<Record<string, unknown>>(`/research/${runId}`);
      const trustScores = res.trust_score;
      return {
        ...res,
        id: String(res.id || res.research_run_id || runId),
        user_id: String(res.user_id || ''),
        company_id: String(res.company_id || ''),
        report_id: res.report_id ? String(res.report_id) : undefined,
        trust_score: trustScores,
      } as unknown as ResearchRun;
    } catch {
      const { data, error } = await supabase
        .from('research_runs')
        .select('*, company:companies(*), trust_scores(*), reports(*)')
        .eq('id', runId)
        .single();

      if (error) throw error;
      const item = data as Record<string, unknown>;
      const trustScores = item.trust_scores as unknown[];
      const trustScore = Array.isArray(trustScores) && trustScores.length > 0 ? trustScores[0] : undefined;
      const reports = item.reports as unknown[];
      const reportId = Array.isArray(reports) && reports.length > 0 ? (reports[0] as Record<string, unknown>).id as string : undefined;

      return {
        ...item,
        id: String(item.id || runId),
        report_id: reportId,
        trust_score: trustScore,
      } as unknown as ResearchRun;
    }
  },

  async getResearchHistory(limit: number = 50): Promise<ResearchRun[]> {
    try {
      const list = await apiClient.get<Record<string, unknown>[]>('/history', {
        params: { limit },
      });
      return (list || []).map((item) => ({
        ...item,
        id: String(item.id || item.research_run_id || ''),
        report_id: item.report_id ? String(item.report_id) : undefined,
      })) as unknown as ResearchRun[];
    } catch {
      const { data, error } = await supabase
        .from('research_runs')
        .select('*, company:companies(*), trust_scores(*), reports(*)')
        .order('created_at', { ascending: false })
        .limit(limit);

      if (error) throw error;
      return (data || []).map((item: Record<string, unknown>) => {
        const trustScores = item.trust_scores as unknown[];
        const trustScore = Array.isArray(trustScores) && trustScores.length > 0 ? trustScores[0] : undefined;
        const reports = item.reports as unknown[];
        const reportId = Array.isArray(reports) && reports.length > 0 ? (reports[0] as Record<string, unknown>).id as string : undefined;
        return {
          ...item,
          id: String(item.id || ''),
          report_id: reportId,
          trust_score: trustScore,
        } as unknown as ResearchRun;
      });
    }
  },
};
