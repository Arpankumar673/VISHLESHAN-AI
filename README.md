# Vishleshan AI

**AI-Powered Company Intelligence, Verification & Trust Analysis Platform**

Vishleshan AI is an evidence-backed company intelligence system designed to verify organizations, analyze hiring and corporate signals, compute deterministic trust and risk scores, and present explainable intelligence reports with clickable source provenance.

---

## Core Product Principles

* **Evidence First**: All factual claims must be supported by verifiable sources.
* **Semantic Verification States**: `Verified`, `Unverified`, `Conflicting`, `Unable to Verify`.
* **Explicit Uncertainty**: Missing evidence is not automatically interpreted as fraud.
* **Deterministic Algorithms**: Trust and risk scoring engines are versioned and reproducible in Python.

---

## Project Structure

```text
VISHLESHAN AI/
├── frontend/         # React, Vite, TypeScript, Tailwind CSS v4, Lucide
├── backend/          # FastAPI, Pydantic, Python Services & Repositories
├── algorithms/       # Deterministic Evidence Fusion, Trust & Risk Engines
├── database/         # Database utilities & seed scripts
├── supabase/         # Migrations and Supabase local configuration
├── n8n/              # Orchestration workflows
├── tests/            # End-to-end and unit test suites
└── docs/             # Technical specifications & roadmap documentation
```

---

## Getting Started

### Prerequisites
* Node.js (v18+)
* Python (v3.10+)
* Supabase Account / CLI

### Frontend Setup
```bash
cd frontend
npm install
npm run dev
```

### Environment Configuration
Copy `.env.example` to `frontend/.env.local` and configure your Supabase credentials:
```env
VITE_SUPABASE_URL=https://your-project.supabase.co
VITE_SUPABASE_PUBLISHABLE_KEY=your-publishable-key
VITE_API_BASE_URL=http://localhost:8000/api
```
