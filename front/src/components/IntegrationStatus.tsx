import React from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { useCurrentHousehold } from '@/hooks/use-current-household';
import { useTodayTasks } from '@/hooks/use-task-occurrences';

const IntegrationStatus: React.FC = () => {
    const { householdId, householdName, loading: householdLoading, error: householdError } = useCurrentHousehold();
    const {
        tasks,
        loading: tasksLoading,
        error: tasksError,
        todayStats,
        tasksByStatus
    } = useTodayTasks(householdId);

    return (
        <Card className="w-full max-w-2xl mx-auto mt-4">
            <CardHeader>
                <CardTitle>État de l'intégration API</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
                <div className="grid grid-cols-2 gap-4">
                    <div>
                        <h4 className="font-semibold mb-2">Household Hook</h4>
                        <div className="space-y-1">
                            <Badge variant={householdLoading ? "secondary" : householdError ? "destructive" : "default"}>
                                {householdLoading ? "Chargement..." : householdError ? "Erreur" : "OK"}
                            </Badge>
                            {householdId && (
                                <p className="text-sm text-gray-600">ID: {householdId}</p>
                            )}
                            {householdName && (
                                <p className="text-sm text-gray-600">Nom: {householdName}</p>
                            )}
                            {householdError && (
                                <p className="text-sm text-red-600">Erreur: {householdError}</p>
                            )}
                        </div>
                    </div>

                    <div>
                        <h4 className="font-semibold mb-2">Tasks Hook</h4>
                        <div className="space-y-1">
                            <Badge variant={tasksLoading ? "secondary" : tasksError ? "destructive" : "default"}>
                                {tasksLoading ? "Chargement..." : tasksError ? "Erreur" : "OK"}
                            </Badge>
                            <p className="text-sm text-gray-600">Tâches: {tasks.length}</p>
                            {tasksError && (
                                <p className="text-sm text-red-600">Erreur: {tasksError}</p>
                            )}
                        </div>
                    </div>
                </div>

                {todayStats && (
                    <div>
                        <h4 className="font-semibold mb-2">Statistiques du jour</h4>
                        <div className="grid grid-cols-4 gap-2 text-sm">
                            <div className="text-center">
                                <div className="font-bold">{todayStats.total}</div>
                                <div className="text-gray-600">Total</div>
                            </div>
                            <div className="text-center">
                                <div className="font-bold text-green-600">{todayStats.completed}</div>
                                <div className="text-gray-600">Terminées</div>
                            </div>
                            <div className="text-center">
                                <div className="font-bold text-orange-600">{todayStats.overdue}</div>
                                <div className="text-gray-600">En retard</div>
                            </div>
                            <div className="text-center">
                                <div className="font-bold text-blue-600">{todayStats.todo}</div>
                                <div className="text-gray-600">À faire</div>
                            </div>
                        </div>
                    </div>
                )}

                {tasksByStatus && (
                    <div>
                        <h4 className="font-semibold mb-2">Répartition des tâches</h4>
                        <div className="space-y-1 text-sm">
                            <p>Terminées: {tasksByStatus.completed.length}</p>
                            <p>En retard: {tasksByStatus.overdue.length}</p>
                            <p>À faire: {tasksByStatus.todo.length}</p>
                        </div>
                    </div>
                )}
            </CardContent>
        </Card>
    );
};

export default IntegrationStatus;
