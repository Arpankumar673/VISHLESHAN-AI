# Vishleshan AI — API Specification

**Base URL**: `/api/v1`

All responses follow standard envelope structures.

### Standard Response Envelope

#### Success Response
```json
{
  "data": { ... }
}
```

#### Error Response
```json
{
  "error": {
    "code": "ERROR_CODE",
    "message": "Human-readable description",
    "details": null
  }
}
```

---

## Endpoints

### 1. Health

#### `GET /api/v1/health`
Returns service operational status.

```json
{
  "status": "ok",
  "service": "vishleshan-api",
  "version": "1.0.0"
}
```

#### `GET /api/v1/health/database`
Checks database connectivity without exposing connection secrets.

```json
{
  "status": "ok",
  "database": "connected",
  "latency_ms": 14.2,
  "service": "vishleshan-api"
}
```

---

### 2. Companies

#### `GET /api/v1/companies/{company_id}`
* **Auth**: Required (Bearer JWT)
* **Response**: `ApiResponse[CompanyResponse]`

#### `GET /api/v1/companies/{company_id}/evidence`
* **Auth**: Required (Bearer JWT)
* **Response**: `ApiResponse[List[EvidenceResponse]]`

---

### 3. Research Runs

#### `POST /api/v1/research`
* **Auth**: Required (Bearer JWT)
* **Request**:
```json
{
  "company_name": "Infosys Limited",
  "company_url": "infosys.com"
}
```
* **Response (201 Created)**:
```json
{
  "data": {
    "research_run_id": "93a62dd9-07b9-4a0b-8d0b-22bca671c668",
    "company_id": "49d8858e-01b4-4e2b-bfe6-a97920e06001",
    "status": "queued"
  }
}
```

#### `GET /api/v1/research/{research_run_id}`
* **Auth**: Required (Owner only)
* **Response**: `ApiResponse[ResearchRunResponse]`

---

### 4. Audit History

#### `GET /api/v1/history?page=1&page_size=20&status=completed`
* **Auth**: Required (Scoped to authenticated user)
* **Response**: `ApiResponse[PaginatedData[ResearchRunResponse]]`

---

### 5. Evidence

#### `GET /api/v1/evidence/{evidence_id}`
* **Auth**: Required
* **Response**: `ApiResponse[EvidenceResponse]`

---

### 6. Intelligence Reports

#### `GET /api/v1/reports/{report_id}`
* **Auth**: Required (Owner only)
* **Response**: `ApiResponse[ReportResponse]`
