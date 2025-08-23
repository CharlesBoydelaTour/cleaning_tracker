import { useEffect, useState } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import { useAuth } from '@/contexts/AuthContext';
import axios from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

export default function AcceptInvite() {
    const location = useLocation();
    const navigate = useNavigate();
    const { isAuthenticated } = useAuth();
    const [status, setStatus] = useState<'pending' | 'success' | 'error'>('pending');
    const [message, setMessage] = useState<string>('Traitement de votre invitation...');

    useEffect(() => {
        const params = new URLSearchParams(location.search);
        const token = params.get('token');
        const hid = params.get('hid');

        if (!token || !hid) {
            setStatus('error');
            setMessage("Lien d'invitation invalide.");
            return;
        }

        const accept = async () => {
            try {
                if (!isAuthenticated) {
                    // L’utilisateur a peut-être ouvert via magic link qui gère la session; sinon, rediriger vers login
                    // On laisse une note, mais on essaie quand même l’appel: si 401, on redirige
                }

                const accessToken = localStorage.getItem('access_token');
                const res = await axios.post(
                    `${API_BASE_URL}/households/${hid}/invites/${token}/accept`,
                    {},
                    {
                        headers: accessToken ? { Authorization: `Bearer ${accessToken}` } : undefined,
                    }
                );

                if (res.status === 200) {
                    setStatus('success');
                    setMessage('Invitation acceptée. Bienvenue dans le foyer !');
                    setTimeout(() => navigate('/home'), 1200);
                } else {
                    setStatus('error');
                    setMessage("Impossible d'accepter l'invitation.");
                }
            } catch (err: any) {
                const sc = err?.response?.status;
                if (sc === 401) {
                    // Non authentifié → rediriger vers login en conservant le lien
                    navigate(`/login?redirect=${encodeURIComponent(location.pathname + location.search)}`);
                    return;
                }
                setStatus('error');
                setMessage(err?.response?.data?.detail || "Erreur lors de l'acceptation de l'invitation.");
            }
        };

        accept();
    }, [location, navigate, isAuthenticated]);

    return (
        <div className="min-h-screen flex items-center justify-center">
            <div className="max-w-md w-full text-center p-6">
                {status === 'pending' && (
                    <>
                        <div className="h-8 w-8 border-4 border-blue-600 border-t-transparent rounded-full animate-spin mx-auto mb-4" />
                        <p className="text-gray-600">{message}</p>
                    </>
                )}
                {status === 'success' && (
                    <p className="text-green-600 font-medium">{message}</p>
                )}
                {status === 'error' && (
                    <p className="text-red-600 font-medium">{message}</p>
                )}
            </div>
        </div>
    );
}
