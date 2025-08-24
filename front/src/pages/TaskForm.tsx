import React, { useEffect, useState } from 'react';
import { ArrowLeft } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { useToast } from '@/hooks/use-toast';
import AppLayout from '@/components/AppLayout';
import { Link, useNavigate, useParams } from 'react-router-dom';
import { useCurrentHousehold } from '@/hooks/use-current-household';
import api from '@/services/api';
import TaskWizard from '@/components/TaskWizard';
import { taskDefinitionsService } from '@/services/task-definitions.service';
import { taskOccurrencesService } from '@/services/task-occurrences.service';

const TaskForm = () => {
  const { id } = useParams(); // ici, id = task definition id
  const navigate = useNavigate();
  const { toast } = useToast();
  const isEdit = Boolean(id);
  const { householdId, householdName } = useCurrentHousehold();
  const [isLoading, setIsLoading] = useState(false);
  const [initial, setInitial] = useState<any | null>(null);

  useEffect(() => {
    const load = async () => {
      if (!householdId) return;
      try {
        if (isEdit && id) {
          const { data } = await api.get(`/households/${householdId}/task-definitions/${id}`);
          setInitial({
            title: data.title || '',
            description: data.description || '',
            room_id: data.room_id || '',
            estimated_minutes: data.estimated_minutes ?? null,
            assigned_to: null,
            recurrence_rule: data.recurrence_rule || 'FREQ=WEEKLY',
            priority: data.priority || 'medium',
            start_date: data.start_date || undefined,
          });
        }
      } catch (e: any) {
        toast({ title: 'Erreur', description: e?.message || 'Chargement impossible', variant: 'destructive' });
      }
    };
    load();
  }, [householdId, id, isEdit]);

  const onWizardSubmit = async (payload: any) => {
    setIsLoading(true);
    try {
      if (!householdId) throw new Error('Aucun foyer actif');
      if (isEdit && id) {
        await api.put(`/households/${householdId}/task-definitions/${id}`, payload);
        toast({ title: 'Tâche mise à jour', description: 'La tâche a été modifiée.' });
      } else {
        await api.post(`/households/${householdId}/task-definitions`, { ...payload, household_id: householdId });
        toast({ title: 'Tâche créée', description: 'La tâche a été ajoutée.' });
      }
      const params = new URLSearchParams(window.location.search);
      const occId = params.get('occurrenceId');
      if (occId && payload.assigned_to) {
        await taskOccurrencesService.assign(occId, payload.assigned_to);
        toast({ title: 'Réassignée', description: 'Occurrence réassignée au membre sélectionné.' });
      }
      navigate('/dashboard?refresh=1');
    } catch (error: any) {
      toast({ title: 'Erreur', description: error?.message || (isEdit ? 'Échec de la mise à jour.' : 'Échec de la création.'), variant: 'destructive' });
    } finally {
      setIsLoading(false);
    }
  };

  const handleDelete = async () => {
    if (!householdId || !id) return;
    if (!confirm('Supprimer définitivement cette tâche ?')) return;
    try {
      await taskDefinitionsService.delete(householdId, id);
      toast({ title: 'Tâche supprimée' });
      // Hint pour le Dashboard: ajouter un flag dans l'URL pour forcer un refresh
      navigate('/dashboard?refresh=1');
    } catch (e: any) {
      toast({ title: 'Erreur', description: e?.message || 'Suppression impossible', variant: 'destructive' });
    }
  };

  const handleReopenToday = async () => {
    try {
      const params = new URLSearchParams(window.location.search);
      const occId = params.get('occurrenceId');
      if (!occId) {
        toast({ title: 'Info', description: 'Aucune occurrence terminée à rouvrir depuis cet écran.' });
        return;
      }
      await taskOccurrencesService.reopen(occId);
      toast({ title: "Remise à aujourd'hui", description: 'La tâche est de nouveau à faire aujourd\'hui.' });
      navigate('/dashboard');
    } catch (e: any) {
      toast({ title: 'Erreur', description: e?.message || 'Action impossible', variant: 'destructive' });
    }
  };

  return (
    <AppLayout activeHousehold={householdName || 'Foyer'}>
      <main className="container mx-auto px-4 py-6 pb-20 md:pb-6">
        <div className="flex items-center gap-4 mb-6">
          <Button
            variant="ghost"
            size="sm"
            className="p-2"
            onClick={() => {
              if (window.history.length > 1) navigate(-1);
              else navigate('/tasks');
            }}
          >
            <ArrowLeft className="h-4 w-4" />
          </Button>
          <div>
            <h1 className="text-2xl font-bold text-gray-900">
              {isEdit ? 'Modifier la tâche' : 'Créer une tâche'}
            </h1>
            <p className="text-gray-600">
              {isEdit ? 'Mettre à jour la tâche et la planification' : 'Définissez une nouvelle tâche pour votre foyer'}
            </p>
          </div>
        </div>

        <div className="max-w-2xl">
          <Card className="shadow-sm border-0 bg-white">
            <CardHeader>
              <CardTitle className="text-lg font-semibold text-gray-900">{isEdit ? 'Modifier la tâche' : 'Créer une tâche'}</CardTitle>
            </CardHeader>
            <CardContent>
              <TaskWizard
                mode={isEdit ? 'edit' : 'create'}
                householdId={householdId || ''}
                initial={initial || undefined}
                onSubmit={onWizardSubmit}
                onDeleteDefinition={isEdit ? handleDelete : undefined}
                onReopenToday={isEdit ? handleReopenToday : undefined}
              />
              <div className="mt-4">
                <Link to="/tasks">
                  <Button variant="outline" className="border-gray-200 hover:bg-gray-50">Annuler</Button>
                </Link>
              </div>
            </CardContent>
          </Card>
        </div>
      </main>
    </AppLayout>
  );
};

export default TaskForm;
