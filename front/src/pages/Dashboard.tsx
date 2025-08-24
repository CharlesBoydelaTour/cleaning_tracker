import { useEffect, useMemo, useRef, useState } from "react";
import { Calendar, BarChart3, Settings, Plus, CheckCircle2, Clock, AlertTriangle } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Progress } from "@/components/ui/progress";
import { Input } from "@/components/ui/input";
import { Switch } from "@/components/ui/switch";
import { Table, TableBody, TableCaption, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import TaskCard from "@/components/TaskCard";
import AppLayout from "@/components/AppLayout";
import { EmailVerificationBanner } from '@/components/EmailVerificationBanner';
import { useCurrentHousehold } from '@/hooks/use-current-household';
import { useTodayTasks } from '@/hooks/use-task-occurrences';
import { useAuth } from '@/hooks/use-auth';
import NewTaskModal from '@/components/NewTaskModal';
import WelcomeScreen from '@/components/WelcomeScreen';
import CreateHouseholdModal from '@/components/CreateHouseholdModal';
import { taskService } from '@/services/api';
import { taskDefinitionsService, type TaskDefinitionListItem } from '@/services/task-definitions.service';
import { useToast } from '@/hooks/use-toast';
import { useLocation, useNavigate } from 'react-router-dom';

const Dashboard = () => {
    const navigate = useNavigate();
    const location = useLocation();
    const { toast } = useToast();
    const { user, loading: authLoading } = useAuth();
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

    // Scroll targets for stat cards
    const overdueRef = useRef<HTMLDivElement | null>(null);
    const todayRef = useRef<HTMLDivElement | null>(null);
    const completedRef = useRef<HTMLDivElement | null>(null);

    // All task definitions (table)
    const [defs, setDefs] = useState<TaskDefinitionListItem[]>([]);
    const [defsLoading, setDefsLoading] = useState(false);
    const [defsError, setDefsError] = useState<string | null>(null);
    const [defsSearch, setDefsSearch] = useState("");
    const [sortKey, setSortKey] = useState<"title" | "room_name" | "estimated_minutes" | "created_at" | "next_occurrence">("created_at");
    const [sortDir, setSortDir] = useState<"asc" | "desc">("desc");
    const [nextDates, setNextDates] = useState<Record<string, string | null>>({});
    const [onlyTodoToday, setOnlyTodoToday] = useState(false);

    const fetchDefinitions = async () => {
        if (!householdId) return;
        setDefsLoading(true);
        setDefsError(null);
        try {
            const data = await taskDefinitionsService.getByHousehold(householdId);
            setDefs(data);
            // Calculer en arrière-plan la prochaine occurrence pour chaque définition
            Promise.all(
                data.map(async (d) => {
                    try {
                        const dateStr = await taskDefinitionsService.getNextOccurrenceDate(householdId, d.id);
                        return { id: d.id, dateStr } as const;
                    } catch {
                        return { id: d.id, dateStr: null } as const;
                    }
                })
            ).then((pairs) => {
                const map: Record<string, string | null> = {};
                for (const p of pairs) map[p.id] = p.dateStr;
                setNextDates(map);
            });
        } catch (e: any) {
            const msg = e?.message || "Impossible de charger les tâches";
            setDefsError(msg);
            toast({ title: "Erreur", description: msg, variant: "destructive" });
        } finally {
            setDefsLoading(false);
        }
    };

    useEffect(() => {
        if (householdId) fetchDefinitions();
        // Recharger aussi quand on revient/renavigue sur le dashboard
    }, [householdId, location.key]);

    const sortedFilteredDefs = useMemo(() => {
        const q = defsSearch.trim().toLowerCase();
        let items = defs;
        if (q) {
            items = items.filter((d) =>
                d.title.toLowerCase().includes(q) ||
                (d.description?.toLowerCase().includes(q) ?? false) ||
                (d.room_name?.toLowerCase().includes(q) ?? false)
            );
        }
        const sorted = [...items].sort((a, b) => {
            const dir = sortDir === "asc" ? 1 : -1;
            const av = sortKey === 'next_occurrence' ? nextDates[a.id] : (a as any)[sortKey];
            const bv = sortKey === 'next_occurrence' ? nextDates[b.id] : (b as any)[sortKey];
            if (av == null && bv == null) return 0;
            if (av == null) return 1;
            if (bv == null) return -1;
            if (sortKey === "estimated_minutes") {
                return ((av as number) - (bv as number)) * dir;
            }
            return String(av).localeCompare(String(bv)) * dir;
        });
        return sorted;
    }, [defs, defsSearch, sortKey, sortDir, nextDates]);

    // Helper: convert occurrence to TaskCard props
    const convertTaskForCard = (task: any) => {
        // Normaliser la durée estimée à partir de plusieurs sources possibles
        const minutesRaw = task.estimated_minutes ?? task.definition_estimated_minutes ?? task.task_estimated_minutes ?? task.estimatedDuration;
        const minutes = typeof minutesRaw === 'string' ? parseInt(minutesRaw, 10) : minutesRaw;
        const safeMinutes = Number.isFinite(minutes) && minutes > 0 ? minutes : (Number.isFinite(minutes) ? minutes : 0);
        return ({
            id: task.id,
            title: task.definition_title || task.task_title || 'Tâche sans titre',
            description: task.definition_description || task.task_description || '',
            room: task.room_name || 'Aucune pièce',
            assignee: task.assigned_user_name || task.assigned_user_email || 'Non assigné',
            // Durée estimée (min)
            estimatedDuration: safeMinutes,
            status: task.status === 'done' ? 'completed' as const :
                task.status === 'overdue' ? 'overdue' as const :
                    'todo' as const,
            dueTime: task.due_at ? new Date(task.due_at).toLocaleTimeString('fr-FR', {
                hour: '2-digit',
                minute: '2-digit'
            }) : '',
            completedAt: task.status === 'done' ? 'Terminé' : undefined,
            recurrence: 'Récurrent',
            priority: (task.priority || task.definition_priority || 'medium') as 'low' | 'medium' | 'high',
            definitionId: task.task_id || task.definition_id || task.definitionId
        });
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

    // Rafraîchir les tâches du jour au retour/renavigation
    useEffect(() => {
        if (householdId) refetchTasks();
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [householdId, location.key]);

    // Pré-calculs dépendants des tâches (doivent rester avant tout retour conditionnel pour conserver l'ordre des hooks)
    const completedTasks = tasksByStatus?.completed || [];
    const todoTasks = tasksByStatus?.todo || [];
    // Map des définitions pour lesquelles il existe une occurrence à faire aujourd'hui (pending/snoozed)
    const todoTodayMap = useMemo(() => {
        const m: Record<string, boolean> = {};
        // Inclure aussi les en retard comme "à faire aujourd'hui"
        const actionable = [
            ...(tasksByStatus?.todo || []),
            ...(tasksByStatus?.overdue || [])
        ];
        for (const occ of actionable) {
            if (occ.task_id) m[occ.task_id] = true;
        }
        return m;
    }, [todoTasks, tasksByStatus?.overdue]);
    const overdueTasks = tasksByStatus?.overdue || [];
    const completionRate = todayStats ? todayStats.completionRate : 0;

    const handleCreateTask = async (taskData: any) => {
        if (!householdId) {
            alert("Aucun foyer sélectionné pour créer la tâche.");
            return;
        }
        try {
            await taskService.createTask(householdId, taskData);
            await refetchTasks();
            await fetchDefinitions();
        } catch (error: any) {
            toast({ title: 'Erreur', description: error?.message || 'Échec de la création', variant: 'destructive' });
        }
    };

    // Auth and household loading/empty states
    if (authLoading) {
        return (
            <AppLayout activeHousehold="Chargement...">
                <div className="container mx-auto px-4 py-6 text-center">Chargement des informations utilisateur...</div>
            </AppLayout>
        );
    }

    if (!user) {
        return (
            <AppLayout activeHousehold="Connexion requise">
                <div className="container mx-auto px-4 py-6 text-center">Veuillez vous connecter pour accéder à cette page.</div>
            </AppLayout>
        );
    }

    if (householdLoading) {
        return (
            <AppLayout activeHousehold="Chargement...">
                <div className="container mx-auto px-4 py-6 text-center">Chargement des informations du foyer...</div>
            </AppLayout>
        );
    }

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



    return (
        <AppLayout activeHousehold={householdName || "Foyer"}>
            <div className="container mx-auto px-4">
                <EmailVerificationBanner />
            </div>

            <main className="container mx-auto px-4 py-6 pb-20 md:pb-6">
                {/* Overview */}
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
                            <button className="text-center cursor-pointer" onClick={() => todayRef.current?.scrollIntoView({ behavior: 'smooth' })}>
                                <div className="text-2xl font-bold text-gray-900">{todayStats?.total || 0}</div>
                                <div className="text-sm text-gray-600">Total des tâches</div>
                            </button>
                            <button className="text-center cursor-pointer" onClick={() => completedRef.current?.scrollIntoView({ behavior: 'smooth' })}>
                                <div className="text-2xl font-bold text-green-600">{todayStats?.completed || 0}</div>
                                <div className="text-sm text-gray-600">Terminées</div>
                            </button>
                            <button className="text-center cursor-pointer" onClick={() => overdueRef.current?.scrollIntoView({ behavior: 'smooth' })}>
                                <div className="text-2xl font-bold text-orange-600">{todayStats?.overdue || 0}</div>
                                <div className="text-sm text-gray-600">En retard</div>
                            </button>
                            <button className="text-center cursor-pointer" onClick={() => todayRef.current?.scrollIntoView({ behavior: 'smooth' })}>
                                <div className="text-2xl font-bold text-blue-600">{todayStats?.todo || 0}</div>
                                <div className="text-sm text-gray-600">Restantes</div>
                            </button>
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
                    <Button className="w-full sm:w-auto" onClick={() => setShowNewTaskModal(true)}>
                        <Plus className="w-4 h-4 mr-2" />
                        Nouvelle tâche
                    </Button>

                    <Button variant="outline" className="flex-shrink-0 border-gray-200 hover:bg-gray-50" onClick={() => navigate('/calendar')}>
                        <Calendar className="h-4 w-4 mr-2" />
                        Calendrier
                    </Button>
                    <Button variant="outline" className="flex-shrink-0 border-gray-200 hover:bg-gray-50" onClick={() => navigate('/statistics')}>
                        <BarChart3 className="h-4 w-4 mr-2" />
                        Statistiques
                    </Button>
                    <Button variant="outline" className="flex-shrink-0 border-gray-200 hover:bg-gray-50" onClick={() => navigate('/profile')}>
                        <Settings className="h-4 w-4 mr-2" />
                        Paramètres
                    </Button>
                    <Button variant="outline" className="flex-shrink-0 border-gray-200 hover:bg-gray-50" onClick={() => { refetchTasks(); fetchDefinitions(); }}>
                        Rafraîchir
                    </Button>
                </div>

                {/* Overdue Tasks */}
                {overdueTasks.length > 0 && (
                    <div className="mb-6" ref={overdueRef}>
                        <div className="flex items-center gap-2 mb-4">
                            <AlertTriangle className="h-5 w-5 text-red-600" />
                            <h2 className="text-lg font-semibold text-red-700">Tâches en retard</h2>
                            <Badge variant="destructive" className="bg-red-100 text-red-800 border-red-200">{overdueTasks.length}</Badge>
                        </div>
                        <div className="space-y-3">
                            {overdueTasks.map(task => (
                                <TaskCard
                                    key={task.id}
                                    task={convertTaskForCard(task)}
                                    onComplete={() => completeTask(task.id, {})}
                                    onEdit={(definitionId: string) => navigate(`/tasks/${definitionId}/edit?occurrenceId=${task.id}`)}
                                />
                            ))}
                        </div>
                    </div>
                )}

                {/* Today's Tasks */}
                <div className="mb-6" ref={todayRef}>
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
                                    onEdit={(definitionId: string) => navigate(`/tasks/${definitionId}/edit?occurrenceId=${task.id}`)}
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
                    <div ref={completedRef}>
                        <div className="flex items-center gap-2 mb-4">
                            <CheckCircle2 className="h-5 w-5 text-green-600" />
                            <h2 className="text-lg font-semibold text-gray-900">Terminées aujourd'hui</h2>
                            <Badge variant="secondary" className="bg-green-50 text-green-700 border-green-200">{completedTasks.length}</Badge>
                        </div>
                        <div className="space-y-3">
                            {completedTasks.map(task => (
                                <TaskCard key={task.id} task={convertTaskForCard(task)} onEdit={(definitionId: string) => navigate(`/tasks/${definitionId}/edit?occurrenceId=${task.id}`)} />
                            ))}
                        </div>
                    </div>
                )}

                {/* Empty state */}
                {todayTasks.length === 0 && overdueTasks.length === 0 && todoTasks.length === 0 && completedTasks.length === 0 && (
                    <div className="text-center py-12 text-gray-500">
                        <Calendar className="h-16 w-16 mx-auto mb-4 text-gray-300" />
                        <h3 className="text-xl font-medium mb-2">Aucune tâche pour aujourd'hui</h3>
                        <p className="text-sm mb-4">Profitez de votre journée libre ou ajoutez de nouvelles tâches !</p>
                        <Button className="bg-blue-600 hover:bg-blue-700 text-white" onClick={() => setShowNewTaskModal(true)}>
                            <Plus className="h-4 w-4 mr-2" />
                            Ajouter une tâche
                        </Button>
                    </div>
                )}

                {/* All Tasks (Definitions) Table */}
                <Card className="mt-8 shadow-sm border-0 bg-white">
                    <CardHeader className="pb-3">
                        <div className="flex items-center justify-between">
                            <CardTitle className="text-lg font-semibold text-gray-900">Toutes les tâches</CardTitle>
                            <Badge variant="secondary" className="bg-gray-50 text-gray-700 border-gray-200">{defs.length}</Badge>
                        </div>
                        <div className="mt-3 flex flex-col gap-3 md:flex-row md:items-center md:justify-between">
                            <Input
                                placeholder="Rechercher par titre, pièce..."
                                value={defsSearch}
                                onChange={(e) => setDefsSearch(e.target.value)}
                                className="md:max-w-md"
                            />
                            <label className="flex items-center gap-2 text-sm text-gray-700">
                                <Switch checked={onlyTodoToday} onCheckedChange={(v) => setOnlyTodoToday(Boolean(v))} />
                                Afficher seulement à faire aujourd'hui
                            </label>
                        </div>
                    </CardHeader>
                    <CardContent>
                        {defsLoading ? (
                            <div className="text-center py-8 text-gray-500">Chargement des tâches...</div>
                        ) : defsError ? (
                            <div className="text-center py-8 text-red-600">{defsError}</div>
                        ) : defs.length === 0 ? (
                            <div className="text-center py-8 text-gray-500">
                                Aucune tâche définie pour ce foyer.
                                <div className="mt-3">
                                    <Button onClick={() => setShowNewTaskModal(true)}>Créer une tâche</Button>
                                </div>
                            </div>
                        ) : (
                            <Table>
                                <TableHeader>
                                    <TableRow>
                                        <TableHead className="cursor-pointer" onClick={() => { setSortKey('title'); setSortDir(sortKey === 'title' && sortDir === 'asc' ? 'desc' : 'asc'); }}>Titre {sortKey === 'title' ? (sortDir === 'asc' ? '▲' : '▼') : ''}</TableHead>
                                        <TableHead className="cursor-pointer" onClick={() => { setSortKey('room_name'); setSortDir(sortKey === 'room_name' && sortDir === 'asc' ? 'desc' : 'asc'); }}>Pièce {sortKey === 'room_name' ? (sortDir === 'asc' ? '▲' : '▼') : ''}</TableHead>
                                        <TableHead className="cursor-pointer" onClick={() => { setSortKey('estimated_minutes'); setSortDir(sortKey === 'estimated_minutes' && sortDir === 'asc' ? 'desc' : 'asc'); }}>Durée estimée {sortKey === 'estimated_minutes' ? (sortDir === 'asc' ? '▲' : '▼') : ''}</TableHead>
                                        <TableHead>À faire aujourd'hui ?</TableHead>
                                        <TableHead>Récurrence</TableHead>
                                        <TableHead className="cursor-pointer" onClick={() => { setSortKey('next_occurrence'); setSortDir(sortKey === 'next_occurrence' && sortDir === 'asc' ? 'desc' : 'asc'); }}>Prochaine Occurence {sortKey === 'next_occurrence' ? (sortDir === 'asc' ? '▲' : '▼') : ''}</TableHead>
                                        <TableHead className="cursor-pointer" onClick={() => { setSortKey('created_at'); setSortDir(sortKey === 'created_at' && sortDir === 'asc' ? 'desc' : 'asc'); }}>Créée le {sortKey === 'created_at' ? (sortDir === 'asc' ? '▲' : '▼') : ''}</TableHead>
                                        <TableHead>Actions</TableHead>
                                    </TableRow>
                                </TableHeader>
                                <TableBody>
                                    {(onlyTodoToday ? sortedFilteredDefs.filter((d) => todoTodayMap[d.id]) : sortedFilteredDefs).map((d) => (
                                        <TableRow key={d.id}>
                                            <TableCell className="font-medium">{d.title}</TableCell>
                                            <TableCell>{d.room_name ?? '—'}</TableCell>
                                            <TableCell>{typeof d.estimated_minutes === 'number' ? `${d.estimated_minutes} min` : '—'}</TableCell>
                                            <TableCell>{todoTodayMap[d.id] ? 'Oui' : 'Non'}</TableCell>
                                            <TableCell>
                                                <Badge variant="secondary" className="bg-gray-100 text-gray-700 border-gray-200">
                                                    {d.recurrence_rule?.toUpperCase().includes('COUNT=1') ? 'Unique' : 'Récurrente'}
                                                </Badge>
                                            </TableCell>
                                            <TableCell>{nextDates[d.id] ? new Date(nextDates[d.id] as string).toLocaleDateString('fr-FR') : '—'}</TableCell>
                                            <TableCell>{new Date(d.created_at).toLocaleDateString('fr-FR')}</TableCell>
                                            <TableCell>
                                                <div className="flex gap-2">
                                                    <Button variant="outline" size="sm" className="border-gray-200" onClick={() => navigate(`/tasks/${d.id}/edit`)}>
                                                        Modifier
                                                    </Button>
                                                </div>
                                            </TableCell>
                                        </TableRow>
                                    ))}
                                </TableBody>
                                <TableCaption>Liste des définitions de tâches du foyer</TableCaption>
                            </Table>
                        )}
                    </CardContent>
                </Card>
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
