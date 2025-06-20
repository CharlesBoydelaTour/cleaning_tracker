import { useState, useEffect } from 'react';
import { authService } from '@/services/api';

export interface User {
  id: string;
  email: string;
  email_verified: boolean;
  user_metadata?: Record<string, any>;
}

export const useAuth = () => {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [isServerDown, setIsServerDown] = useState(false);

  useEffect(() => {
    const initAuth = async () => {
      try {
        const token = localStorage.getItem('access_token');
        if (!token) {
          setLoading(false);
          return;
        }

        const userProfile = await authService.getCurrentUser();
        setUser(userProfile);
        setError(null);
        setIsServerDown(false);
      } catch (error: any) {
        console.error('Erreur d\'authentification:', error);
        
        if (error.isServerDown) {
          setIsServerDown(true);
          setError('Mode demo - Serveur indisponible');
          // En mode demo, on garde un utilisateur fictif avec un UUID valide
          setUser({
            id: '00000000-0000-0000-0000-000000000000',
            email: 'demo@example.com',
            email_verified: true
          });
        } else {
          localStorage.removeItem('access_token');
          localStorage.removeItem('refresh_token');
          setUser(null);
          setError('Session expirée, veuillez vous reconnecter');
        }
      } finally {
        setLoading(false);
      }
    };

    initAuth();
  }, []);

  const login = async (email: string, password: string) => {
    try {
      setLoading(true);
      setError(null);
      const response = await authService.login({ email, password });
      localStorage.setItem('access_token', response.tokens.access_token);
      localStorage.setItem('refresh_token', response.tokens.refresh_token);
      setUser(response.user);
      
      // Vérifier si c'est le mode demo
      if (response.tokens.access_token === 'demo-token') {
        setIsServerDown(true);
        setError('Mode demo - Serveur indisponible');
      }
      
      return response;
    } catch (error: any) {
      if (error.isServerDown) {
        setIsServerDown(true);
        setError('Mode demo - Serveur indisponible');
        // Permettre la connexion en mode demo
        return;
      }
      
      const errorMessage = error.response?.data?.detail || 'Erreur de connexion';
      setError(errorMessage);
      throw error;
    } finally {
      setLoading(false);
    }
  };

  const signup = async (email: string, password: string) => {
    try {
      setLoading(true);
      setError(null);
      const response = await authService.register({ email, password });
      localStorage.setItem('access_token', response.tokens.access_token);
      localStorage.setItem('refresh_token', response.tokens.refresh_token);
      setUser(response.user);
      
      if (response.tokens.access_token === 'demo-token') {
        setIsServerDown(true);
        setError('Mode demo - Serveur indisponible');
      }
      
      return response;
    } catch (error: any) {
      if (error.isServerDown) {
        setIsServerDown(true);
        setError('Mode demo - Serveur indisponible');
        return;
      }
      
      const errorMessage = error.response?.data?.detail || 'Erreur d\'inscription';
      setError(errorMessage);
      throw error;
    } finally {
      setLoading(false);
    }
  };

  const logout = () => {
    localStorage.removeItem('access_token');
    localStorage.removeItem('refresh_token');
    setUser(null);
    setError(null);
    setIsServerDown(false);
  };

  return {
    user,
    loading,
    error,
    isServerDown,
    login,
    signup,
    logout,
    isAuthenticated: !!user
  };
};