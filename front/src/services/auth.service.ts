import apiClient from '@/lib/api-client';
import type { AuthResponse, LoginCredentials, SignupData, User } from '@/types';

export const authService = {
  async login(credentials: LoginCredentials): Promise<AuthResponse> {
    const response = await apiClient.post<AuthResponse>('/auth/login', credentials);
    return response.data;
  },

  async signup(data: SignupData): Promise<AuthResponse> {
    const response = await apiClient.post<AuthResponse>('/auth/signup', data);
    return response.data;
  },

  async logout(): Promise<void> {
    await apiClient.post('/auth/logout');
    localStorage.removeItem('access_token');
    localStorage.removeItem('refresh_token');
  },

  async getCurrentUser(): Promise<User> {
    const response = await apiClient.get<User>('/auth/me');
    return response.data;
  },

  async updateProfile(data: { full_name?: string; email?: string }): Promise<User> {
    const response = await apiClient.put<User>('/auth/me', data);
    return response.data;
  },

  async changePassword(data: { current_password: string; new_password: string }): Promise<void> {
    await apiClient.post('/auth/change-password', data);
  },

  async refreshToken(refreshToken: string): Promise<AuthResponse> {
    const response = await apiClient.post<AuthResponse>('/auth/refresh', {
      refresh_token: refreshToken
    });
    return response.data;
  },

  async requestPasswordReset(email: string): Promise<void> {
    await apiClient.post('/auth/reset-password', { email });
  },

  async deleteAccount(): Promise<void> {
    await apiClient.delete('/auth/me');
    localStorage.removeItem('access_token');
    localStorage.removeItem('refresh_token');
  },

  async resendVerificationEmail(email: string): Promise<void> {
    await apiClient.post('/auth/resend-verification-email', null, {
      params: { email }
    });
  }
};