# Vishleshan AI — Security Architecture & Authentication Model

## 1. Authentication Flow

Vishleshan AI uses Supabase Authentication with JSON Web Tokens (JWT):

1. **Client Authentication**: The React frontend authenticates users directly against Supabase Auth (`supabase.auth.signInWithPassword` or `signUp`).
2. **Token Transmission**: For all protected API requests, the frontend sends the token in the `Authorization` header:
   ```text
   Authorization: Bearer <Supabase access token>
   ```
3. **Backend Validation**:
   - The FastAPI dependency `get_current_user` extracts the token.
   - If `SUPABASE_JWT_SECRET` is configured, it verifies the cryptographic signature (HMAC-SHA256).
   - If offline or secret is omitted, it resolves the user identity via Supabase Auth API or decodes the claims safely.
   - Rejects unauthenticated or malformed requests with `HTTP 401 Unauthorized`.

---

## 2. Resource Ownership Enforcement

To prevent Insecure Direct Object References (IDOR):
* Research runs and reports enforce user identity matching.
* `POST /api/v1/research` derives ownership strictly from `current_user.id` rather than request body parameters.
* `GET /api/v1/research/{id}` and `GET /api/v1/reports/{id}` verify that `run.user_id == current_user.id` and reject unauthorized access with `HTTP 403 Forbidden`.
* `GET /api/v1/history` automatically queries exclusively under the authenticated `user_id`.

---

## 3. Secret Management & Separation of Concerns

| Key / Secret | Storage Location | Accessible in Frontend? |
| :--- | :--- | :--- |
| `VITE_SUPABASE_URL` | `frontend/.env.local` | Yes (Public) |
| `VITE_SUPABASE_PUBLISHABLE_KEY` | `frontend/.env.local` | Yes (Public) |
| `SUPABASE_SERVICE_ROLE_KEY` | `backend/.env` (Server only) | **NO** |
| `SUPABASE_JWT_SECRET` | `backend/.env` (Server only) | **NO** |
| `N8N_WEBHOOK_SECRET` | `backend/.env` (Server only) | **NO** |
