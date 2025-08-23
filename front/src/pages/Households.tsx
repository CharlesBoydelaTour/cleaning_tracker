
import React, { useState } from 'react';
import { Home, Plus } from 'lucide-react';
import { useQuery } from '@tanstack/react-query';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter } from '@/components/ui/dialog';
import AppLayout from '@/components/AppLayout';
import { Link, useNavigate } from 'react-router-dom';
import { householdsService } from '@/services/households.service';
import { useCurrentHousehold } from '@/hooks/use-current-household';
import type { Household } from '@/types';

const Households = () => {
  const navigate = useNavigate();
  const { householdName, selectHousehold, refetch: refetchCurrent } = useCurrentHousehold();
  const [open, setOpen] = useState(false);
  const [newName, setNewName] = useState('');
  const [creating, setCreating] = useState(false);
  const {
    data: households = [],
    isLoading,
    isError,
    refetch,
  } = useQuery<Household[]>({
    queryKey: ['households'],
    queryFn: householdsService.getAll,
  });

  const onCreate = async () => {
    if (!newName.trim()) return;
    setCreating(true);
    try {
      const created = await householdsService.create({ name: newName.trim() });
      setOpen(false);
      setNewName('');
      await refetch();
      // Sélectionner ce nouveau foyer et naviguer vers sa page
      if (created?.id) {
        selectHousehold(created.id);
        await refetchCurrent();
        navigate(`/households/${created.id}`);
      }
    } finally {
      setCreating(false);
    }
  };

  return (
    <AppLayout activeHousehold={householdName ?? undefined}>
      <main className="container mx-auto px-4 py-6 pb-20 md:pb-6">
        <div className="flex items-center justify-between mb-6">
          <h1 className="text-2xl font-bold text-gray-900">My Households</h1>
          <Button className="bg-blue-600 hover:bg-blue-700 text-white" onClick={() => setOpen(true)}>
            <Plus className="h-4 w-4 mr-2" />
            Create Household
          </Button>
        </div>

        {isLoading && <p>Loading households...</p>}
        {isError && (
          <div className="text-center py-6">
            <p className="mb-2">Failed to load households.</p>
            <Button variant="outline" onClick={() => refetch()}>
              Retry
            </Button>
          </div>
        )}

        {!isLoading && !isError && (
          <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
            {households.map((household) => (
              <Card key={household.id} className="shadow-sm border-0 bg-white hover:shadow-md transition-shadow">
                <CardHeader className="pb-3">
                  <div className="flex items-center gap-3">
                    <div className="h-10 w-10 bg-blue-100 rounded-lg flex items-center justify-center">
                      <Home className="h-5 w-5 text-blue-600" />
                    </div>
                    <CardTitle className="text-lg font-semibold text-gray-900">
                      {household.name}
                    </CardTitle>
                  </div>
                </CardHeader>
                <CardContent className="pt-0">
                  <Link to={`/households/${household.id}`} className="flex-1">
                    <Button variant="outline" size="sm" className="w-full border-gray-200 hover:bg-gray-50">
                      Manage
                    </Button>
                  </Link>
                </CardContent>
              </Card>
            ))}
          </div>
        )}

        {!isLoading && !isError && households.length === 0 && (
          <div className="text-center py-12">
            <Home className="h-16 w-16 text-gray-300 mx-auto mb-4" />
            <h3 className="text-lg font-semibold text-gray-900 mb-2">No households yet</h3>
            <p className="text-gray-600 mb-6">Create your first household to start organizing chores.</p>
            <Button className="bg-blue-600 hover:bg-blue-700 text-white" onClick={() => setOpen(true)}>
              <Plus className="h-4 w-4 mr-2" />
              Create Your First Household
            </Button>
          </div>
        )}

        <Dialog open={open} onOpenChange={setOpen}>
          <DialogContent>
            <DialogHeader>
              <DialogTitle>Create a household</DialogTitle>
            </DialogHeader>
            <div className="space-y-3 py-2">
              <Input
                placeholder="Household name"
                value={newName}
                onChange={(e) => setNewName(e.target.value)}
                onKeyDown={(e) => { if (e.key === 'Enter') onCreate(); }}
                autoFocus
              />
            </div>
            <DialogFooter>
              <Button variant="outline" onClick={() => setOpen(false)}>Cancel</Button>
              <Button onClick={onCreate} disabled={creating || !newName.trim()}>
                {creating ? 'Creating…' : 'Create'}
              </Button>
            </DialogFooter>
          </DialogContent>
        </Dialog>
      </main>
    </AppLayout>
  );
};

export default Households;
