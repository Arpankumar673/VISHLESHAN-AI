import { supabase } from '../lib/supabase';
import type { Profile, SignInPayload, SignUpPayload } from '../types';

export const authService = {
  async signIn({ email, password }: SignInPayload) {
    return supabase.auth.signInWithPassword({ email, password });
  },

  async signUp({ email, password, fullName }: SignUpPayload) {
    return supabase.auth.signUp({
      email,
      password,
      options: {
        data: {
          full_name: fullName,
        },
      },
    });
  },

  async signOut() {
    return supabase.auth.signOut();
  },

  async resetPasswordForEmail(email: string, redirectTo?: string) {
    const defaultRedirect = `${window.location.origin}/reset-password`;
    return supabase.auth.resetPasswordForEmail(email, {
      redirectTo: redirectTo || defaultRedirect,
    });
  },

  async updateUserPassword(password: string) {
    return supabase.auth.updateUser({ password });
  },

  async getSession() {
    return supabase.auth.getSession();
  },

  async getCurrentUser() {
    const {
      data: { user },
    } = await supabase.auth.getUser();
    return user;
  },

  async getProfile(userId: string): Promise<Profile | null> {
    const { data, error } = await supabase
      .from('profiles')
      .select('*')
      .eq('id', userId)
      .maybeSingle();

    if (error) {
      throw error;
    }
    return data as Profile | null;
  },

  async updateProfile(userId: string, updates: Partial<Profile>) {
    const { data, error } = await supabase
      .from('profiles')
      .update(updates)
      .eq('id', userId)
      .select()
      .single();

    if (error) {
      throw error;
    }
    return data as Profile;
  },
};
