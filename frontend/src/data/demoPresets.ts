export interface DemoPreset {
  id: string;
  display_name: string;
  company_name: string;
  official_url: string | null;
  requires_manual_url?: boolean;
}

export const DEMO_PRESETS: DemoPreset[] = [
  {
    id: 'hackindia',
    display_name: 'HackIndia',
    company_name: 'HackIndia',
    official_url: null,
    requires_manual_url: true,
  },
  {
    id: 'hcltech',
    display_name: 'HCLTech',
    company_name: 'HCL Technologies Limited',
    official_url: 'https://www.hcltech.com',
  },
  {
    id: 'hal',
    display_name: 'HAL (Hindustan Aeronautics Ltd)',
    company_name: 'Hindustan Aeronautics Limited',
    official_url: 'https://hal-india.co.in',
  },
  {
    id: 'trianglemind',
    display_name: 'Triangle Mind',
    company_name: 'Triangle Mind',
    official_url: 'https://trianglemind.in',
  },
];
