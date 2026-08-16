import { createContext } from 'react';
import type { Session, User } from '@supabase/supabase-js';
import type { Profile, SignInPayload, SignUpPayload } from '../types';

export interface AuthContextType {
  user: User | null;
  profile: Profile | null;
  session: Session | null;
  loading: boolean;
  initialized: boolean;
  signIn: (payload: SignInPayload) => Promise<{ error: string | null }>;
  signUp: (payload: SignUpPayload) => Promise<{ error: string | null }>;
  signOut: () => Promise<void>;
  resetPassword: (email: string) => Promise<{ error: string | null }>;
  updatePassword: (password: string) => Promise<{ error: string | null }>;
  refreshProfile: () => Promise<void>;
}

export const AuthContext = createContext<AuthContextType | undefined>(undefined);
