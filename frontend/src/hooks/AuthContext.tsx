import React, { useEffect, useState, useCallback } from 'react';
import type { Session, User } from '@supabase/supabase-js';
import { supabase } from '../lib/supabase';
import type { Profile, SignInPayload, SignUpPayload } from '../types';
import { AuthContext } from './authContextValue';

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [user, setUser] = useState<User | null>(null);
  const [profile, setProfile] = useState<Profile | null>(null);
  const [session, setSession] = useState<Session | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [initialized, setInitialized] = useState<boolean>(false);

  const fetchProfile = useCallback(async (userId: string): Promise<Profile | null> => {
    try {
      const { data, error } = await supabase
        .from('profiles')
        .select('*')
        .eq('id', userId)
        .maybeSingle();

      if (error) {
        console.warn('Could not fetch profile from Supabase:', error.message);
        return null;
      }
      return data as Profile | null;
    } catch (err) {
      console.error('Unexpected error fetching profile:', err);
      return null;
    }
  }, []);

  const refreshProfile = useCallback(async () => {
    if (user) {
      const userProfile = await fetchProfile(user.id);
      setProfile(userProfile);
    }
  }, [user, fetchProfile]);

  useEffect(() => {
    let isMounted = true;

    // Get initial session with fail-safe error handling and timeout
    const initTimer = setTimeout(() => {
      if (isMounted) {
        setLoading(false);
        setInitialized(true);
      }
    }, 2500);

    supabase.auth
      .getSession()
      .then(async ({ data: { session: initialSession } }) => {
        if (!isMounted) return;

        setSession(initialSession);
        const currentUser = initialSession?.user ?? null;
        setUser(currentUser);

        if (currentUser) {
          try {
            const userProfile = await fetchProfile(currentUser.id);
            if (isMounted) setProfile(userProfile);
          } catch {
            // Profile fetch optional
          }
        } else {
          if (isMounted) setProfile(null);
        }

        if (isMounted) {
          setLoading(false);
          setInitialized(true);
          clearTimeout(initTimer);
        }
      })
      .catch((err) => {
        console.warn('Could not initialize Supabase session:', err);
        if (isMounted) {
          setLoading(false);
          setInitialized(true);
          clearTimeout(initTimer);
        }
      });

    // Listen for auth state changes
    const { data: { subscription } } = supabase.auth.onAuthStateChange(
      async (_event, newSession) => {
        if (!isMounted) return;

        setSession(newSession);
        const currentUser = newSession?.user ?? null;
        setUser(currentUser);

        if (currentUser) {
          const userProfile = await fetchProfile(currentUser.id);
          if (isMounted) setProfile(userProfile);
        } else {
          if (isMounted) setProfile(null);
        }

        if (isMounted) {
          setLoading(false);
        }
      }
    );

    return () => {
      isMounted = false;
      subscription.unsubscribe();
    };
  }, [fetchProfile]);

  const signIn = async ({ email, password }: SignInPayload) => {
    setLoading(true);
    try {
      const { error } = await supabase.auth.signInWithPassword({
        email,
        password,
      });
      if (error) {
        setLoading(false);
        return { error: error.message };
      }
      return { error: null };
    } catch (err: unknown) {
      setLoading(false);
      const msg = err instanceof Error ? err.message : 'An unexpected error occurred during sign in';
      return { error: msg };
    }
  };

  const signUp = async ({ email, password, fullName }: SignUpPayload) => {
    setLoading(true);
    try {
      const { data, error } = await supabase.auth.signUp({
        email,
        password,
        options: {
          data: {
            full_name: fullName,
          },
        },
      });

      if (error) {
        setLoading(false);
        return { error: error.message };
      }

      if (data.user) {
        try {
          await supabase.from('profiles').upsert({
            id: data.user.id,
            full_name: fullName,
            role: 'user',
          });
        } catch {
          // Handled by DB trigger or RLS
        }
      }

      setLoading(false);
      return { error: null };
    } catch (err: unknown) {
      setLoading(false);
      const msg = err instanceof Error ? err.message : 'An unexpected error occurred during registration';
      return { error: msg };
    }
  };

  const signOut = async () => {
    setLoading(true);
    try {
      await supabase.auth.signOut();
      setUser(null);
      setProfile(null);
      setSession(null);
    } finally {
      setLoading(false);
    }
  };

  const resetPassword = async (email: string) => {
    try {
      const redirectTo = `${window.location.origin}/reset-password`;
      const { error } = await supabase.auth.resetPasswordForEmail(email, {
        redirectTo,
      });
      if (error) {
        return { error: error.message };
      }
      return { error: null };
    } catch (err: unknown) {
      const msg =
        err instanceof Error ? err.message : 'Failed to send password reset email';
      return { error: msg };
    }
  };

  const updatePassword = async (password: string) => {
    try {
      const { error } = await supabase.auth.updateUser({ password });
      if (error) {
        return { error: error.message };
      }
      return { error: null };
    } catch (err: unknown) {
      const msg =
        err instanceof Error ? err.message : 'Failed to update password';
      return { error: msg };
    }
  };

  return (
    <AuthContext.Provider
      value={{
        user,
        profile,
        session,
        loading,
        initialized,
        signIn,
        signUp,
        signOut,
        resetPassword,
        updatePassword,
        refreshProfile,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
};
