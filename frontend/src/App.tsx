import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider } from './hooks/AuthContext';
import { ProtectedRoute } from './components/common/ProtectedRoute';
import { PublicOnlyRoute } from './components/common/PublicOnlyRoute';
import { AppLayout } from './layouts/AppLayout';
import { AuthLayout } from './layouts/AuthLayout';

import {
  Landing,
  Login,
  Register,
  ForgotPassword,
  ResetPassword,
  Dashboard,
  Research,
  ResearchProgress,
  Report,
  History,
  EvidenceExplorer,
  AskAI,
} from './pages';

function App() {
  return (
    <AuthProvider>
      <BrowserRouter>
        <Routes>
          {/* Public Landing Page */}
          <Route path="/" element={<Landing />} />

          {/* Authentication Routes (Public Only) */}
          <Route element={<PublicOnlyRoute />}>
            <Route element={<AuthLayout />}>
              <Route path="/login" element={<Login />} />
              <Route path="/register" element={<Register />} />
              <Route path="/forgot-password" element={<ForgotPassword />} />
            </Route>
          </Route>

          {/* Password Reset Route (Supports Recovery Sessions and Public Links) */}
          <Route element={<AuthLayout />}>
            <Route path="/reset-password" element={<ResetPassword />} />
          </Route>

          {/* Protected Application Routes */}
          <Route element={<ProtectedRoute />}>
            <Route element={<AppLayout />}>
              <Route path="/dashboard" element={<Dashboard />} />
              <Route path="/research" element={<Research />} />
              <Route path="/research/:runId" element={<ResearchProgress />} />
              <Route path="/reports/:reportId" element={<Report />} />
              <Route path="/history" element={<History />} />
              <Route path="/evidence/:id" element={<EvidenceExplorer />} />
              <Route path="/ask" element={<AskAI />} />
            </Route>
          </Route>

          {/* Catch-all Redirect */}
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </BrowserRouter>
    </AuthProvider>
  );
}

export default App;
