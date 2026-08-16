import { apiClient } from './api';
import { supabase } from '../lib/supabase';
import type { Evidence } from '../types';

export const evidenceService = {
  async getEvidence(evidenceId: string): Promise<Evidence> {
    try {
      return await apiClient.get<Evidence>(`/evidence/${evidenceId}`);
    } catch {
      const { data, error } = await supabase
        .from('evidence')
        .select('*')
        .eq('id', evidenceId)
        .single();

      if (error) throw error;
      return data as Evidence;
    }
  },

  async getEvidenceForCompany(companyId: string): Promise<Evidence[]> {
    try {
      return await apiClient.get<Evidence[]>(`/companies/${companyId}/evidence`);
    } catch {
      const { data, error } = await supabase
        .from('evidence')
        .select('*')
        .eq('company_id', companyId)
        .order('observed_at', { ascending: false });

      if (error) throw error;
      return (data || []) as Evidence[];
    }
  },

  async getEvidenceForRun(runId: string): Promise<Evidence[]> {
    try {
      return await apiClient.get<Evidence[]>(`/research/${runId}/evidence`);
    } catch {
      const { data, error } = await supabase
        .from('evidence')
        .select('*')
        .eq('research_run_id', runId)
        .order('observed_at', { ascending: false });

      if (error) throw error;
      return (data || []) as Evidence[];
    }
  },
};
