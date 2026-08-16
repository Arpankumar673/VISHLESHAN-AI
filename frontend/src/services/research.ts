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
      // In M2 / before FastAPI M3 is up, we can prepare the run record in Supabase
      const { data: { user } } = await supabase.auth.getUser();
      if (!user) throw new Error('User must be authenticated to start research');

      const normalizedName = payload.company_name.toLowerCase().trim();

      // Find or insert company
      let companyId: string;
      const { data: existingCompany } = await supabase
        .from('companies')
        .select('id')
        .eq('normalized_name', normalizedName)
        .maybeSingle();

      if (existingCompany) {
        companyId = existingCompany.id;
      } else {
        const { data: newCompany, error: createError } = await supabase
          .from('companies')
          .insert({
            name: payload.company_name,
            normalized_name: normalizedName,
            official_domain: payload.company_url || null,
          })
          .select('id')
          .single();

        if (createError) throw createError;
        companyId = newCompany.id;
      }

      // Create research run
      const { data: run, error: runError } = await supabase
        .from('research_runs')
        .insert({
          user_id: user.id,
          company_id: companyId,
          status: 'queued',
          started_at: new Date().toISOString(),
        })
        .select('id, status')
        .single();

      if (runError) throw runError;

      return {
        research_run_id: run.id,
        company_id: companyId,
        status: run.status,
      };
    }
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
