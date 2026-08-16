export type UserRole = 'user' | 'admin' | 'researcher';

export interface Profile {
  id: string;
  full_name: string | null;
  role: UserRole;
  created_at: string;
  updated_at: string;
}

export interface AuthUser {
  id: string;
  email?: string;
  user_metadata?: {
    full_name?: string;
    [key: string]: unknown;
  };
}

export interface AuthState {
  user: AuthUser | null;
  profile: Profile | null;
  session: unknown | null;
  loading: boolean;
  initialized: boolean;
}

export interface SignInPayload {
  email: string;
  password: string;
}

export interface SignUpPayload {
  email: string;
  password: string;
  fullName: string;
}
