export interface Household {
  id: string;
  name: string;
  created_at: string;
}

export interface HouseholdMember {
  id: string;
  household_id: string;
  user_id: string; // Gardé pour référence interne si nécessaire
  role: 'admin' | 'member' | 'guest';
  joined_at?: string;
  user_full_name?: string; // Ajouté
  user_email?: string;     // Ajouté
}

export interface Room {
  id: string;
  household_id: string;
  name: string;
  icon?: string;
  created_at?: string;
}

export interface HouseholdCreate {
  name: string;
}

export interface HouseholdMemberCreate {
  user_id: string;
  role?: 'admin' | 'member' | 'guest';
}