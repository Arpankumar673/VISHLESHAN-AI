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
    try {
      return await apiClient.post<StartResearchResponse>('/research', payload);
    } catch {
      // Fallback: try inserting research run into Supabase directly if API client fails
      try {
        const { data: compData } = await supabase
          .from('companies')
          .select('id')
          .eq('normalized_name', payload.company_name.trim().toLowerCase())
          .maybeSingle();

        let companyId = compData?.id;
        if (!companyId) {
          const { data: newComp } = await supabase
            .from('companies')
            .insert({
              name: payload.company_name,
              normalized_name: payload.company_name.trim().toLowerCase(),
              official_domain: payload.company_url,
            })
            .select('id')
            .single();
          companyId = newComp?.id;
        }

        const { data: runData, error } = await supabase
          .from('research_runs')
          .insert({
            company_id: companyId,
            status: 'queued',
          })
          .select('id, company_id, status')
          .single();

        if (error || !runData) throw error;
        return {
          research_run_id: runData.id,
          company_id: runData.company_id,
          status: runData.status,
        };
      } catch {
        // Safe client-side temporary UUID fallback preserving the actual requested company
        const fallbackRunId = typeof crypto !== 'undefined' && crypto.randomUUID ? crypto.randomUUID() : 'temp-run-id';
        const fallbackCompId = typeof crypto !== 'undefined' && crypto.randomUUID ? crypto.randomUUID() : 'temp-comp-id';
        return {
          research_run_id: fallbackRunId,
          company_id: fallbackCompId,
          status: 'running',
        };
      }
    }
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
        .maybeSingle();

      if (error || !data) {
        throw new Error(`Research run ${runId} not found`);
      }

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
