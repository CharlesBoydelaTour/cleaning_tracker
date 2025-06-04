import { useEffect } from 'react';
import { authService } from '@/services/auth.service';
import apiClient from '@/lib/api-client';

export function useTokenRefresh() {
  useEffect(() => {
    // Intercepteur pour rafraîchir le token automatiquement
    const interceptor = apiClient.interceptors.response.use(
      (response) => response,
      async (error) => {
        const originalRequest = error.config;

       if (error.response?.status === 401 && !originalRequest._retry) {
         originalRequest._retry = true;

         try {
           const refreshToken = localStorage.getItem('refresh_token');
           if (!refreshToken) {
             throw new Error('No refresh token');
           }

           const response = await authService.refreshToken(refreshToken);
           localStorage.setItem('access_token', response.tokens.access_token);
           localStorage.setItem('refresh_token', response.tokens.refresh_token);

           // Retry la requête originale avec le nouveau token
           originalRequest.headers.Authorization = `Bearer ${response.tokens.access_token}`;
           return apiClient(originalRequest);
         } catch (refreshError) {
           // Échec du refresh, rediriger vers login
           localStorage.removeItem('access_token');
           localStorage.removeItem('refresh_token');
           window.location.href = '/login';
           return Promise.reject(refreshError);
         }
       }

       return Promise.reject(error);
     }
   );

   // Cleanup
   return () => {
     apiClient.interceptors.response.eject(interceptor);
   };
 }, []);
}