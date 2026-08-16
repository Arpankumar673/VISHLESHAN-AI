import { apiClient } from './api';
import { supabase } from '../lib/supabase';
import type { Company, CompanyIdentifier } from '../types';

export const companyService = {
  async getCompany(companyId: string): Promise<Company> {
    try {
      return await apiClient.get<Company>(`/companies/${companyId}`);
    } catch {
      // Fallback to Supabase direct client if FastAPI is not yet running
      const { data, error } = await supabase
        .from('companies')
        .select('*')
        .eq('id', companyId)
        .single();

      if (error) throw error;
      return data as Company;
    }
  },

  async listCompanies(limit: number = 20): Promise<Company[]> {
    try {
      return await apiClient.get<Company[]>('/companies', {
        params: { limit },
      });
    } catch {
      const { data, error } = await supabase
        .from('companies')
        .select('*')
        .order('created_at', { ascending: false })
        .limit(limit);

      if (error) throw error;
      return (data || []) as Company[];
    }
  },

  async getCompanyIdentifiers(companyId: string): Promise<CompanyIdentifier[]> {
    try {
      return await apiClient.get<CompanyIdentifier[]>(
        `/companies/${companyId}/identifiers`
      );
    } catch {
      const { data, error } = await supabase
        .from('company_identifiers')
        .select('*')
        .eq('company_id', companyId);

      if (error) throw error;
      return (data || []) as CompanyIdentifier[];
    }
  },
};
