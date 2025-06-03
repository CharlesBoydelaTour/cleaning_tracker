// Re-export tous les types
export * from './auth.types';
export * from './household.types';
export * from './task.types';

// Types utilitaires
export interface ApiError {
  error: {
    code: string;
    message: string;
    severity: string;
    metadata?: Record<string, any>;
  };
}

export interface PaginatedResponse<T> {
  data: T[];
  total: number;
  page: number;
  per_page: number;
}