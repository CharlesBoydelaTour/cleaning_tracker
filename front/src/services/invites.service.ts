import axios from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

const api = axios.create({ baseURL: API_BASE_URL, timeout: 10000 });
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('access_token');
  if (token) config.headers.Authorization = `Bearer ${token}`;
  return config;
});

export interface UserInvite {
  id: string;
  household_id: string;
  household_name: string;
  role: 'admin' | 'member' | 'guest';
  status: 'pending' | 'accepted' | 'revoked' | 'expired';
  created_at: string;
  expires_at?: string | null;
}

export const invitesService = {
  listMine: async (): Promise<UserInvite[]> => {
    const res = await api.get('/invites');
    return res.data as UserInvite[];
  },
  accept: async (inviteId: string): Promise<void> => {
    await api.post(`/invites/${inviteId}/accept`);
  },
  decline: async (inviteId: string): Promise<void> => {
    await api.post(`/invites/${inviteId}/decline`);
  },
};
