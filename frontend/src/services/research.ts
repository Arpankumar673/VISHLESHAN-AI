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
      return await apiClient.get<ResearchRun>(`/research/${runId}`);
    } catch {
      const { data, error } = await supabase
        .from('research_runs')
        .select('*, company:companies(*), trust_scores(*)')
        .eq('id', runId)
        .single();

      if (error) throw error;
      const item = data as Record<string, unknown>;
      const trustScores = item.trust_scores as unknown[];
      const trustScore = Array.isArray(trustScores) && trustScores.length > 0 ? trustScores[0] : undefined;

      return {
        ...item,
        trust_score: trustScore,
      } as unknown as ResearchRun;
    }
  },

  async getResearchHistory(limit: number = 50): Promise<ResearchRun[]> {
    try {
      return await apiClient.get<ResearchRun[]>('/history', {
        params: { limit },
      });
    } catch {
      const { data, error } = await supabase
        .from('research_runs')
        .select('*, company:companies(*), trust_scores(*)')
        .order('created_at', { ascending: false })
        .limit(limit);

      if (error) throw error;
      return (data || []).map((item: Record<string, unknown>) => {
        const trustScores = item.trust_scores as unknown[];
        const trustScore = Array.isArray(trustScores) && trustScores.length > 0 ? trustScores[0] : undefined;
        return {
          ...item,
          trust_score: trustScore,
        } as unknown as ResearchRun;
      });
    }
  },
};
