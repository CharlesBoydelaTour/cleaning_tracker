import React, { createContext, useContext, useState, useEffect, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { authService } from '@/services/auth.service';
import type { User, LoginCredentials, SignupData } from '@/types';
import { useToast } from '@/hooks/use-toast';

interface AuthContextType {
    user: User | null;
    isLoading: boolean;
    isAuthenticated: boolean;
    login: (credentials: LoginCredentials) => Promise<void>;
    signup: (data: SignupData) => Promise<void>;
    logout: () => Promise<void>;
    refreshUser: () => Promise<void>;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export function AuthProvider({ children }: { children: React.ReactNode }) {
    const [user, setUser] = useState<User | null>(null);
    const [isLoading, setIsLoading] = useState(true);
    const navigate = useNavigate();
    const { toast } = useToast();

    // Fonction pour décoder le JWT et extraire l'utilisateur
    const getUserFromToken = (token: string): Partial<User> | null => {
        try {
            const payload = JSON.parse(atob(token.split('.')[1]));
            return {
                id: payload.sub,
                email: payload.email,
            };
        } catch {
            return null;
        }
    };

    // Vérifier si l'utilisateur est connecté au chargement
    useEffect(() => {
        checkAuth();
    }, []);

    const checkAuth = async () => {
        const token = localStorage.getItem('access_token');
        if (!token) {
            setIsLoading(false);
            return;
        }

        try {
            // Décoder le token pour obtenir les infos de base
            const tokenUser = getUserFromToken(token);
            if (!tokenUser) {
                throw new Error('Invalid token');
            }

            // Essayer de récupérer les infos complètes de l'utilisateur
            try {
                const currentUser = await authService.getCurrentUser();
                setUser(currentUser);
            } catch (error) {
                // Si l'API échoue, utiliser les infos du token
                setUser(tokenUser as User);
            }
        } catch (error) {
            // Token invalide ou expiré
            localStorage.removeItem('access_token');
            localStorage.removeItem('refresh_token');
            setUser(null);
        } finally {
            setIsLoading(false);
        }
    };

    const login = useCallback(async (credentials: LoginCredentials) => {
        try {
            const response = await authService.login(credentials);

            // Stocker les tokens
            localStorage.setItem('access_token', response.tokens.access_token);
            localStorage.setItem('refresh_token', response.tokens.refresh_token);

            // Mettre à jour l'utilisateur
            setUser(response.user);

            // Rediriger vers le dashboard
            navigate('/');

            toast({
                title: "Connexion réussie",
                description: `Bienvenue ${response.user.full_name || response.user.email}!`,
            });
        } catch (error: any) {
            const message = error.response?.data?.error?.message || "Email ou mot de passe incorrect";
            throw new Error(message);
        }
    }, [navigate, toast]);

    const signup = useCallback(async (data: SignupData) => {
        try {
            const response = await authService.signup(data);

            // Stocker les tokens
            localStorage.setItem('access_token', response.tokens.access_token);
            localStorage.setItem('refresh_token', response.tokens.refresh_token);

            // Mettre à jour l'utilisateur
            setUser(response.user);

            // Afficher un message sur la vérification email
            toast({
                title: "Compte créé avec succès",
                description: "Un email de vérification vous a été envoyé. Veuillez vérifier votre boîte de réception.",
                duration: 10000, // Afficher plus longtemps
            });

            // Rediriger vers le dashboard
            navigate('/');

        } catch (error: any) {
            const message = error.response?.data?.error?.message || "Erreur lors de la création du compte";
            throw new Error(message);
        }
    }, [navigate, toast]);

    const logout = useCallback(async () => {
        try {
            await authService.logout();
        } catch (error) {
            // Ignorer les erreurs de logout côté serveur
        } finally {
            // Nettoyer le localStorage
            localStorage.removeItem('access_token');
            localStorage.removeItem('refresh_token');

            // Réinitialiser l'utilisateur
            setUser(null);

            // Rediriger vers login
            navigate('/login');

            toast({
                title: "Déconnexion réussie",
                description: "À bientôt!",
            });
        }
    }, [navigate, toast]);

    const refreshUser = useCallback(async () => {
        try {
            const currentUser = await authService.getCurrentUser();
            setUser(currentUser);
        } catch (error) {
            console.error('Failed to refresh user:', error);
        }
    }, []);

    const value = {
        user,
        isLoading,
        isAuthenticated: !!user,
        login,
        signup,
        logout,
        refreshUser,
    };

    return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
    const context = useContext(AuthContext);
    if (context === undefined) {
        throw new Error('useAuth must be used within an AuthProvider');
    }
    return context;
}