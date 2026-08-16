export interface Company {
  id: string;
  name: string;
  normalized_name: string;
  official_domain?: string | null;
  description?: string | null;
  industry?: string | null;
  headquarters?: string | null;
  created_at: string;
  updated_at: string;
}

export interface CompanyIdentifier {
  id: string;
  company_id: string;
  identifier_type: string;
  identifier_value: string;
  source_url?: string | null;
  confidence?: number | null;
  created_at: string;
}
