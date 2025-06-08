import axios from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

// Créer l'instance axios avec gestion d'erreur
const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 10000,
});

// Intercepteur pour ajouter le token
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('access_token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Intercepteur pour gérer les erreurs serveur
api.interceptors.response.use(
  (response) => response,
  (error) => {
    // Si le serveur est down ou erreur 500, utiliser le mode offline
    if (!error.response || error.response.status >= 500) {
      console.warn('Backend indisponible, passage en mode dégradé');
      // Ne pas rediriger, laisser l'app gérer
      return Promise.reject({ 
        ...error, 
        isServerDown: true,
        message: 'Serveur temporairement indisponible'
      });
    }
    
    if (error.response?.status === 401) {
      localStorage.removeItem('access_token');
      localStorage.removeItem('refresh_token');
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);

// Service d'authentification avec fallback
export const authService = {
  async login(credentials: { email: string; password: string }) {
    try {
      const response = await api.post('/auth/login', credentials);
      return response.data;
    } catch (error: any) {
      if (error.isServerDown) {
        // Mode demo pour développement
        return {
          user: {
            id: 'demo-user-id',
            email: credentials.email,
            email_verified: true
          },
          tokens: {
            access_token: 'demo-token',
            refresh_token: 'demo-refresh-token',
            token_type: 'bearer'
          }
        };
      }
      throw error;
    }
  },

  async register(credentials: { email: string; password: string }) {
    try {
      const response = await api.post('/auth/signup', credentials);
      return response.data;
    } catch (error: any) {
      if (error.isServerDown) {
        // Mode demo pour développement
        return {
          user: {
            id: 'demo-user-id',
            email: credentials.email,
            email_verified: true
          },
          tokens: {
            access_token: 'demo-token',
            refresh_token: 'demo-refresh-token',
            token_type: 'bearer'
          }
        };
      }
      throw error;
    }
  },

  async getCurrentUser() {
    try {
      const response = await api.get('/auth/me');
      return response.data;
    } catch (error: any) {
      if (error.isServerDown) {
        // Mode demo pour développement
        return {
          id: 'demo-user-id',
          email: 'demo@example.com',
          email_verified: true
        };
      }
      throw error;
    }
  }
};

// Service pour les ménages avec données de demo
export const householdService = {
  async getHouseholds() {
    try {
      const response = await api.get('/households/');
      return response.data;
    } catch (error: any) {
      if (error.isServerDown) {
        // Données de demo
        return [{
          id: 'demo-household-id',
          name: 'Ma Maison (Demo)',
          created_at: new Date().toISOString()
        }];
      }
      throw error;
    }
  },

  async createHousehold(data: { name: string }) {
    try {
      const response = await api.post('/households/', data);
      return response.data;
    } catch (error: any) {
      if (error.isServerDown) {
        return {
          id: 'demo-household-id',
          name: data.name,
          created_at: new Date().toISOString()
        };
      }
      throw error;
    }
  }
};

// Service pour les tâches avec données de demo
export const taskService = {
  async getTodayTasks(householdId: string) {
    try {
      const response = await api.get(`/task-occurrences/today?household_id=${householdId}`);
      return response.data;
    } catch (error: any) {
      if (error.isServerDown) {
        // Données de demo
        return {
          tasks: [
            {
              id: 'demo-task-1',
              definition_title: 'Faire la vaisselle',
              definition_description: 'Nettoyer la vaisselle du petit-déjeuner',
              room_name: 'Cuisine',
              assigned_user_name: 'Demo User',
              estimated_minutes: 15,
              status: 'pending',
              due_at: new Date().toISOString()
            },
            {
              id: 'demo-task-2',
              definition_title: 'Passer l\'aspirateur',
              definition_description: 'Aspirer le salon et la salle à manger',
              room_name: 'Salon',
              assigned_user_name: 'Demo User',
              estimated_minutes: 30,
              status: 'pending',
              due_at: new Date(Date.now() + 2 * 60 * 60 * 1000).toISOString()
            }
          ],
          stats: {
            total: 2,
            completed: 0,
            pending: 2,
            overdue: 0
          }
        };
      }
      throw error;
    }
  },

  async completeTask(taskId: string) {
    try {
      const response = await api.post(`/task-occurrences/${taskId}/complete`);
      return response.data;
    } catch (error: any) {
      if (error.isServerDown) {
        return { success: true, message: 'Tâche complétée (mode demo)' };
      }
      throw error;
    }
  },

  async snoozeTask(taskId: string, snoozeUntil: string) {
    try {
      const response = await api.post(`/task-occurrences/${taskId}/snooze`, { snooze_until: snoozeUntil });
      return response.data;
    } catch (error: any) {
      if (error.isServerDown) {
        return { success: true, message: 'Tâche reportée (mode demo)' };
      }
      throw error;
    }
  },

  async skipTask(taskId: string) {
    try {
      const response = await api.post(`/task-occurrences/${taskId}/skip`);
      return response.data;
    } catch (error: any) {
      if (error.isServerDown) {
        return { success: true, message: 'Tâche ignorée (mode demo)' };
      }
      throw error;
    }
  },

async createTask(householdId: string, taskData: any) {
  console.log('taskService.createTask appelé:', { householdId, taskData });
  
  try {
    const requestData = {
      ...taskData,
      household_id: householdId
    };
    
    console.log('Données de la requête:', requestData);
    console.log('URL de la requête:', `${API_BASE_URL}/households/${householdId}/task-definitions`);
    
    const response = await api.post(`/households/${householdId}/task-definitions`, requestData);
    
    console.log('Réponse de l\'API:', response.data);
    return response.data;
  } catch (error: any) {
    console.error('Erreur dans createTask:', error);
    
    if (error.isServerDown) {
      console.log('Mode demo activé');
      // Mode demo
      const demoResult = {
        id: `demo-task-${Date.now()}`,
        ...taskData,
        created_at: new Date().toISOString()
      };
      console.log('Retour demo:', demoResult);
      return demoResult;
    }
    throw error;
  }
}
};