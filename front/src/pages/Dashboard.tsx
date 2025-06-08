import { useState } from "react";
import { Calendar, BarChart3, Settings, Plus, CheckCircle2, Clock, AlertTriangle } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Progress } from "@/components/ui/progress";
import TaskCard from "@/components/TaskCard";
import AppLayout from "@/components/AppLayout";
import { EmailVerificationBanner } from '@/components/EmailVerificationBanner';
import IntegrationStatus from '@/components/IntegrationStatus';
import { useCurrentHousehold } from '@/hooks/use-current-household';
import { useTodayTasks } from '@/hooks/use-task-occurrences';
import { useAuth } from '@/hooks/use-auth';
import NewTaskModal from '@/components/NewTaskModal';
import { taskService } from '@/services/api';
import WelcomeScreen from '@/components/WelcomeScreen';
import CreateHouseholdModal from '@/components/CreateHouseholdModal';

const Dashboard = () => {
    const { user, loading: authLoading, isServerDown } = useAuth();
    const {
        householdId,
        householdName,
        loading: householdLoading,
        currentHousehold,
        error: householdError,
        refetch: refetchHousehold
    } = useCurrentHousehold();

    const tasksHookResult = useTodayTasks(householdId);

    const [showNewTaskModal, setShowNewTaskModal] = useState(false);
    const [showCreateHouseholdModal, setShowCreateHouseholdModal] = useState(false);

    // 1. Gérer le chargement de l'authentification
    if (authLoading) {
        return (
            <AppLayout activeHousehold="Chargement...">
                <div className="container mx-auto px-4 py-6 text-center">Chargement des informations utilisateur...</div>
            </AppLayout>
        );
    }

    // 2. Gérer le cas où l'utilisateur n'est pas authentifié
    if (!user) {
        return (
            <AppLayout activeHousehold="Connexion requise">
                <div className="container mx-auto px-4 py-6 text-center">Veuillez vous connecter pour accéder à cette page.</div>
            </AppLayout>
        );
    }

    // 3. Gérer le chargement du ménage
    if (householdLoading) {
        return (
            <AppLayout activeHousehold="Chargement...">
                <div className="container mx-auto px-4 py-6 text-center">Chargement des informations du foyer...</div>
            </AppLayout>
        );
    }

    // 4. Gérer l'erreur de chargement du ménage
    if (householdError) {
        return (
            <AppLayout activeHousehold="Erreur">
                <div className="container mx-auto px-4 py-6 text-center">
                    <p className="text-red-600">Erreur lors du chargement du foyer : {householdError}</p>
                    <Button onClick={() => refetchHousehold && refetchHousehold()} className="mt-2">
                        Réessayer
                    </Button>
                </div>
            </AppLayout>
        );
    }

    // 5. Si l'utilisateur est authentifié, le chargement du ménage est terminé, sans erreur, MAIS aucun ménage n'est trouvé
    if (!currentHousehold) {
        return (
            <AppLayout activeHousehold="Bienvenue">
                <WelcomeScreen onCreateHousehold={() => setShowCreateHouseholdModal(true)} />
                <CreateHouseholdModal
                    open={showCreateHouseholdModal}
                    onOpenChange={setShowCreateHouseholdModal}
                    onSuccess={() => {
                        setShowCreateHouseholdModal(false);
                        if (refetchHousehold) {
                            refetchHousehold();
                        } else {
                            window.location.reload();
                        }
                    }}
                />
            </AppLayout>
        );
    }

    const {
        tasks: todayTasks,
        loading: tasksLoading,
        error: tasksError,
        todayStats,
        tasksByStatus,
        completeTask,
        snoozeTask,
        skipTask,
        refetch: refetchTasks
    } = tasksHookResult;

    // 6. Gérer le chargement des tâches
    if (tasksLoading) {
        return (
            <AppLayout activeHousehold={householdName || "Chargement..."}>
                <div className="container mx-auto px-4 py-6">
                    <div className="flex items-center justify-center h-64">
                        <div className="text-center">
                            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mx-auto"></div>
                            <p className="mt-2 text-gray-600">Chargement des tâches...</p>
                        </div>
                    </div>
                </div>
            </AppLayout>
        );
    }

    // 7. Gérer l'erreur de chargement des tâches
    if (tasksError) {
        return (
            <AppLayout activeHousehold={householdName || "Erreur"}>
                <div className="container mx-auto px-4 py-6">
                    <div className="flex items-center justify-center h-64">
                        <div className="text-center">
                            <p className="text-red-600">Erreur lors du chargement des tâches : {tasksError}</p>
                            <Button onClick={refetchTasks} className="mt-2">
                                Réessayer
                            </Button>
                        </div>
                    </div>
                </div>
            </AppLayout>
        );
    }

    // Helper function to convert API task to TaskCard format
    const convertTaskForCard = (task: any) => ({
        id: task.id,
        title: task.definition_title || task.task_title || 'Tâche sans titre',
        description: task.definition_description || task.task_description || '',
        room: task.room_name || 'Aucune pièce',
        assignee: task.assigned_user_name || task.assigned_user_email || 'Non assigné',
        estimatedDuration: task.estimated_minutes || 0,
        status: task.status === 'done' ? 'completed' as const :
            task.status === 'overdue' ? 'overdue' as const :
                'todo' as const,
        dueTime: task.due_at ? new Date(task.due_at).toLocaleTimeString('fr-FR', {
            hour: '2-digit',
            minute: '2-digit'
        }) : '',
        completedAt: task.status === 'done' ? 'Terminé' : undefined,
        recurrence: 'Récurrent'
    });

    const handleCreateTask = async (taskData: any) => {
        if (!householdId) {
            alert("Aucun foyer sélectionné pour créer la tâche.");
            return;
        }
        console.log('handleCreateTask appelé avec:', taskData);
        try {
            console.log('Appel de taskService.createTask...');
            const result = await taskService.createTask(householdId, taskData);
            console.log('Résultat de la création:', result);
            await refetchTasks();
            console.log('Données rafraîchies');
        } catch (error: any) {
            console.error('Erreur lors de la création de la tâche:', error);
            alert('Erreur lors de la création de la tâche: ' + error.message);
        }
    };

    const completedTasks = tasksByStatus?.completed || [];
    const overdueTasks = tasksByStatus?.overdue || [];
    const todoTasks = tasksByStatus?.todo || [];
    const completionRate = todayStats ? todayStats.completionRate : 0;

    return (
        <AppLayout activeHousehold={householdName || "Foyer"}>
            <div className="container mx-auto px-4">
                <EmailVerificationBanner />
                <IntegrationStatus />
            </div>

            <main className="container mx-auto px-4 py-6 pb-20 md:pb-6">
                {/* Today Overview Card */}
                <Card className="mb-6 shadow-sm border-0 bg-white">
                    <CardHeader className="pb-4">
                        <div className="flex items-center justify-between">
                            <CardTitle className="text-xl font-semibold text-gray-900">Aperçu d'aujourd'hui</CardTitle>
                            <Badge variant="secondary" className="bg-blue-50 text-blue-700 border-blue-200">
                                {new Date().toLocaleDateString('fr-FR', { weekday: 'long', day: 'numeric', month: 'long' })}
                            </Badge>
                        </div>
                    </CardHeader>
                    <CardContent className="space-y-4">
                        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                            <div className="text-center">
                                <div className="text-2xl font-bold text-gray-900">{todayStats?.total || 0}</div>
                                <div className="text-sm text-gray-600">Total des tâches</div>
                            </div>
                            <div className="text-center">
                                <div className="text-2xl font-bold text-green-600">{todayStats?.completed || 0}</div>
                                <div className="text-sm text-gray-600">Terminées</div>
                            </div>
                            <div className="text-center">
                                <div className="text-2xl font-bold text-orange-600">{todayStats?.overdue || 0}</div>
                                <div className="text-sm text-gray-600">En retard</div>
                            </div>
                            <div className="text-center">
                                <div className="text-2xl font-bold text-blue-600">{todayStats?.todo || 0}</div>
                                <div className="text-sm text-gray-600">Restantes</div>
                            </div>
                        </div>

                        <div className="space-y-2">
                            <div className="flex justify-between text-sm">
                                <span className="text-gray-600">Progrès quotidien</span>
                                <span className="font-medium text-gray-900">{completionRate}% Terminé</span>
                            </div>
                            <Progress value={completionRate} className="h-2" />
                        </div>
                    </CardContent>
                </Card>

                {/* Quick Actions */}
                <div className="flex gap-3 mb-6 overflow-x-auto pb-2">
                    <Button
                        className="w-full sm:w-auto"
                        onClick={() => setShowNewTaskModal(true)}
                    >
                        <Plus className="w-4 h-4 mr-2" />
                        Nouvelle tâche
                    </Button>

                    <Button variant="outline" className="flex-shrink-0 border-gray-200 hover:bg-gray-50">
                        <Calendar className="h-4 w-4 mr-2" />
                        Calendrier
                    </Button>
                    <Button variant="outline" className="flex-shrink-0 border-gray-200 hover:bg-gray-50">
                        <BarChart3 className="h-4 w-4 mr-2" />
                        Statistiques
                    </Button>
                    <Button variant="outline" className="flex-shrink-0 border-gray-200 hover:bg-gray-50">
                        <Settings className="h-4 w-4 mr-2" />
                        Paramètres
                    </Button>
                </div>

                {/* Overdue Tasks */}
                {overdueTasks.length > 0 && (
                    <div className="mb-6">
                        <div className="flex items-center gap-2 mb-4">
                            <AlertTriangle className="h-5 w-5 text-orange-600" />
                            <h2 className="text-lg font-semibold text-gray-900">Tâches en retard</h2>
                            <Badge variant="destructive" className="bg-orange-100 text-orange-800 border-orange-200">
                                {overdueTasks.length}
                            </Badge>
                        </div>
                        <div className="space-y-3">
                            {overdueTasks.map(task => (
                                <TaskCard
                                    key={task.id}
                                    task={convertTaskForCard(task)}
                                    onComplete={() => completeTask(task.id, {})}
                                    onSnooze={() => snoozeTask(task.id, new Date(Date.now() + 60 * 60 * 1000).toISOString())}
                                    onSkip={() => skipTask(task.id, "Tâche ignorée depuis la page d'accueil")}
                                />
                            ))}
                        </div>
                    </div>
                )}

                {/* Today's Tasks */}
                <div className="mb-6">
                    <div className="flex items-center gap-2 mb-4">
                        <Clock className="h-5 w-5 text-blue-600" />
                        <h2 className="text-lg font-semibold text-gray-900">Tâches d'aujourd'hui</h2>
                    </div>
                    {todoTasks.length > 0 ? (
                        <div className="space-y-3">
                            {todoTasks.map(task => (
                                <TaskCard
                                    key={task.id}
                                    task={convertTaskForCard(task)}
                                    onComplete={() => completeTask(task.id, {})}
                                    onSnooze={() => snoozeTask(task.id, new Date(Date.now() + 60 * 60 * 1000).toISOString())}
                                    onSkip={() => skipTask(task.id, "Tâche ignorée depuis la page d'accueil")}
                                />
                            ))}
                        </div>
                    ) : (
                        <div className="text-center py-8 text-gray-500">
                            <CheckCircle2 className="h-12 w-12 mx-auto mb-2 text-green-500" />
                            <p className="text-lg font-medium">Toutes les tâches d'aujourd'hui sont terminées !</p>
                            <p className="text-sm">Bon travail ! 🎉</p>
                        </div>
                    )}
                </div>

                {/* Completed Tasks */}
                {completedTasks.length > 0 && (
                    <div>
                        <div className="flex items-center gap-2 mb-4">
                            <CheckCircle2 className="h-5 w-5 text-green-600" />
                            <h2 className="text-lg font-semibold text-gray-900">Terminées aujourd'hui</h2>
                            <Badge variant="secondary" className="bg-green-50 text-green-700 border-green-200">
                                {completedTasks.length}
                            </Badge>
                        </div>
                        <div className="space-y-3">
                            {completedTasks.map(task => (
                                <TaskCard
                                    key={task.id}
                                    task={convertTaskForCard(task)}
                                />
                            ))}
                        </div>
                    </div>
                )}

                {/* Empty state when no tasks at all for a valid household */}
                {todayTasks.length === 0 && overdueTasks.length === 0 && todoTasks.length === 0 && completedTasks.length === 0 && (
                    <div className="text-center py-12 text-gray-500">
                        <Calendar className="h-16 w-16 mx-auto mb-4 text-gray-300" />
                        <h3 className="text-xl font-medium mb-2">Aucune tâche pour aujourd'hui</h3>
                        <p className="text-sm mb-4">Profitez de votre journée libre ou ajoutez de nouvelles tâches !</p>
                        <Button
                            className="bg-blue-600 hover:bg-blue-700 text-white"
                            onClick={() => setShowNewTaskModal(true)}
                        >
                            <Plus className="h-4 w-4 mr-2" />
                            Ajouter une tâche
                        </Button>
                    </div>
                )}
            </main>

            <NewTaskModal
                isOpen={showNewTaskModal}
                onClose={() => setShowNewTaskModal(false)}
                onSubmit={handleCreateTask}
                householdId={householdId || ''}
            />
        </AppLayout>
    );
};

export default Dashboard;
