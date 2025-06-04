import React, { createContext, useContext, useEffect, useState, useCallback } from 'react';
import { householdsService } from '@/services/households.service';
import type { Household } from '@/types';

interface HouseholdContextType {
  households: Household[];
  activeHousehold: Household | null;
  loading: boolean;
  refreshHouseholds: () => Promise<void>;
  setActiveHousehold: (household: Household) => void;
}

const HouseholdContext = createContext<HouseholdContextType | undefined>(undefined);

export const HouseholdProvider = ({ children }: { children: React.ReactNode }) => {
  const [households, setHouseholds] = useState<Household[]>([]);
  const [activeHousehold, setActiveHousehold] = useState<Household | null>(null);
  const [loading, setLoading] = useState(true);

  const fetchHouseholds = useCallback(async () => {
    setLoading(true);
    try {
      const data = await householdsService.getAll();
      setHouseholds(data);
      if (!activeHousehold && data.length > 0) {
        setActiveHousehold(data[0]);
      }
    } catch (error) {
      console.error('Failed to fetch households', error);
    } finally {
      setLoading(false);
    }
  }, [activeHousehold]);

  useEffect(() => {
    fetchHouseholds();
  }, [fetchHouseholds]);

  return (
    <HouseholdContext.Provider value={{ households, activeHousehold, loading, refreshHouseholds: fetchHouseholds, setActiveHousehold }}>
      {children}
    </HouseholdContext.Provider>
  );
};

export const useHouseholds = () => {
  const ctx = useContext(HouseholdContext);
  if (ctx === undefined) {
    throw new Error('useHouseholds must be used within a HouseholdProvider');
  }
  return ctx;
};
