import React, { useEffect, useMemo, useState } from 'react';
import { ChevronLeft, ChevronRight, Filter, Plus, Calendar as CalendarIcon, Check } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Card, CardContent } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import AppLayout from '@/components/AppLayout';
import { Dialog, DialogContent, DialogTitle, DialogTrigger } from '@/components/ui/dialog';
import { TaskWizard } from '@/components/TaskWizard';
import { taskOccurrencesService } from '@/services/task-occurrences.service';
import { roomsService } from '@/services/rooms.service';
import { membersService } from '@/services/members.service';
import { taskService } from '@/services/api';
import { useCurrentHousehold } from '@/hooks/use-current-household';
import type { TaskOccurrenceWithDefinition, TaskStatus } from '@/types/task.types';
import type { Room, HouseholdMember } from '@/types/household.types';
import { useNavigate } from 'react-router-dom';

const Calendar = () => {
  const [currentDate, setCurrentDate] = useState(new Date());
  const [view, setView] = useState<'day' | 'week' | 'month'>('month');
  const { householdId, householdName } = useCurrentHousehold();
  const [isFiltersOpen, setIsFiltersOpen] = useState(false);
  const [isWizardOpen, setIsWizardOpen] = useState(false);
  const [loading, setLoading] = useState(false);
  const [occurrences, setOccurrences] = useState<TaskOccurrenceWithDefinition[]>([]);
  const [rooms, setRooms] = useState<Room[]>([]);
  const [members, setMembers] = useState<HouseholdMember[]>([]);
  const navigate = useNavigate();

  // Filtres
  const [filterStatuses, setFilterStatuses] = useState<TaskStatus[]>([]); // vide => tous
  const [filterRoomId, setFilterRoomId] = useState<string>('');
  const [filterAssignee, setFilterAssignee] = useState<string>('');
  const [filterPriority, setFilterPriority] = useState<'low' | 'medium' | 'high' | ''>('');

  // Utils dates (locale FR, timezone navigateur)
  const fmt = useMemo(() => (opts: Intl.DateTimeFormatOptions) =>
    new Intl.DateTimeFormat('fr-FR', { timeZone: Intl.DateTimeFormat().resolvedOptions().timeZone, ...opts }), []);

  const formatYMD = (d: Date) => {
    const y = d.getFullYear();
    const m = String(d.getMonth() + 1).padStart(2, '0');
    const day = String(d.getDate()).padStart(2, '0');
    return `${y}-${m}-${day}`;
  };

  const startOfWeek = (d: Date) => {
    const date = new Date(d);
    const day = (date.getDay() + 6) % 7; // Lundi=0
    date.setDate(date.getDate() - day);
    date.setHours(0, 0, 0, 0);
    return date;
  };

  const endOfWeek = (d: Date) => {
    const s = startOfWeek(d);
    const e = new Date(s);
    e.setDate(s.getDate() + 6);
    e.setHours(23, 59, 59, 999);
    return e;
  };

  const startOfMonth = (d: Date) => new Date(d.getFullYear(), d.getMonth(), 1);
  const endOfMonth = (d: Date) => new Date(d.getFullYear(), d.getMonth() + 1, 0);

  const getDaysGridForMonth = (d: Date) => {
    const first = startOfMonth(d);
    const last = endOfMonth(d);
    const leading = (first.getDay() + 6) % 7; // nombre de cases vides avant lundi
    const days: (Date | null)[] = [];
    for (let i = 0; i < leading; i++) days.push(null);
    for (let day = 1; day <= last.getDate(); day++) {
      days.push(new Date(d.getFullYear(), d.getMonth(), day));
    }
    return days;
  };

  const navigateBy = (unit: 'day' | 'week' | 'month', dir: 'prev' | 'next') => {
    setCurrentDate(prev => {
      const n = new Date(prev);
      const delta = dir === 'prev' ? -1 : 1;
      if (unit === 'day') n.setDate(n.getDate() + delta);
      if (unit === 'week') n.setDate(n.getDate() + 7 * delta);
      if (unit === 'month') n.setMonth(n.getMonth() + delta);
      return n;
    });
  };

  const monthLabel = fmt({ month: 'long', year: 'numeric' }).format(currentDate);
  const weekLabel = `${fmt({ day: '2-digit', month: 'short' }).format(startOfWeek(currentDate))} – ${fmt({ day: '2-digit', month: 'short', year: 'numeric' }).format(endOfWeek(currentDate))}`;
  const dayLabel = fmt({ weekday: 'long', day: '2-digit', month: 'long', year: 'numeric' }).format(currentDate);

  const dayNames = ['Lun', 'Mar', 'Mer', 'Jeu', 'Ven', 'Sam', 'Dim'];

  const statusColor = (status: TaskStatus) => {
    switch (status) {
      case 'done': return 'bg-green-500';
      case 'overdue': return 'bg-red-500';
      case 'snoozed': return 'bg-orange-500';
      case 'skipped': return 'bg-gray-400';
      default: return 'bg-blue-500'; // pending
    }
  };

  // Charger rooms/members
  useEffect(() => {
    const loadMeta = async () => {
      if (!householdId) return;
      try {
        const [r, m] = await Promise.all([
          roomsService.getAll(householdId),
          membersService.getAll(householdId)
        ]);
        setRooms(r);
        setMembers(m);
      } catch (e) {
        // silencieux, UI basique sans options
      }
    };
    loadMeta();
  }, [householdId]);

  // Charger occurrences selon la vue/date/filtres principaux
  const fetchOccurrences = async () => {
    if (!householdId) return;
    setLoading(true);
    try {
      let start: Date;
      let end: Date;
      if (view === 'month') { start = startOfMonth(currentDate); end = endOfMonth(currentDate); }
      else if (view === 'week') { start = startOfWeek(currentDate); end = endOfWeek(currentDate); }
      else { start = new Date(currentDate); end = new Date(currentDate); }

      const params: any = {
        start_date: formatYMD(start),
        end_date: formatYMD(end),
      };
      // Optionnellement on peut pré-filtrer côté API par statut unique
      if (filterStatuses.length === 1) params.status = filterStatuses[0];
      if (filterRoomId) params.room_id = filterRoomId;
      if (filterAssignee) params.assigned_to = filterAssignee;

      const data = await taskOccurrencesService.getByHousehold(householdId, params);
      setOccurrences(data);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchOccurrences();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [householdId, view, currentDate, filterRoomId, filterAssignee, filterStatuses.length]);

  // Filtrage client pour la priorité et les multi-statuts
  const filteredOccurrences = useMemo(() => {
    return occurrences.filter(o => {
      const byStatus = filterStatuses.length ? filterStatuses.includes(o.status) : true;
      const byPriority = filterPriority ? (o as any).definition_priority === filterPriority : true;
      return byStatus && byPriority;
    });
  }, [occurrences, filterStatuses, filterPriority]);

  // Groupes par jour
  const occurrencesByDay = useMemo(() => {
    const map: Record<string, TaskOccurrenceWithDefinition[]> = {};
    for (const o of filteredOccurrences) {
      const key = o.scheduled_date; // déjà YYYY-MM-DD
      if (!map[key]) map[key] = [];
      map[key].push(o);
    }
    // trier par due_at si présent
    Object.values(map).forEach(list => list.sort((a, b) => (a.due_at || '').localeCompare(b.due_at || '')));
    return map;
  }, [filteredOccurrences]);

  const toggleStatus = (s: TaskStatus) => {
    setFilterStatuses(prev => prev.includes(s) ? prev.filter(x => x !== s) : [...prev, s]);
  };

  const handleComplete = async (occId: string) => {
    try {
      await taskOccurrencesService.complete(occId, {});
      await fetchOccurrences();
    } catch { }
  };

  const createTask = async (data: any) => {
    if (!householdId) return;
    await taskService.createTask(householdId, data);
    setIsWizardOpen(false);
    await fetchOccurrences();
  };

  return (
    <AppLayout activeHousehold={householdName || undefined}>
      <main className="container mx-auto px-4 py-6 pb-20 md:pb-6">
        <div className="flex items-center justify-between mb-6">
          <h1 className="text-2xl font-bold text-gray-900">Calendrier</h1>
          <div className="flex items-center gap-2">
            <div className="relative">
              <Button variant="outline" onClick={() => setIsFiltersOpen(v => !v)} className="border-gray-200 hover:bg-gray-50">
                <Filter className="h-4 w-4 mr-2" />
                Filtres
              </Button>
              {isFiltersOpen && (
                <div className="absolute right-0 mt-2 w-80 bg-white border border-gray-200 rounded-md shadow-md z-10 p-4 space-y-3">
                  <div>
                    <div className="text-sm font-semibold mb-2">Statuts</div>
                    <div className="flex flex-wrap gap-2">
                      {(['pending', 'done', 'overdue', 'snoozed', 'skipped'] as TaskStatus[]).map(s => (
                        <Button key={s} size="sm" variant={filterStatuses.includes(s) ? 'default' : 'outline'} onClick={() => toggleStatus(s)}>
                          {s}
                        </Button>
                      ))}
                    </div>
                  </div>
                  <div className="grid grid-cols-2 gap-3">
                    <div>
                      <div className="text-sm font-semibold mb-1">Pièce</div>
                      <select className="w-full border rounded px-2 py-1" value={filterRoomId} onChange={e => setFilterRoomId(e.target.value)}>
                        <option value="">Toutes</option>
                        {rooms.map(r => <option key={r.id} value={r.id}>{r.name}</option>)}
                      </select>
                    </div>
                    <div>
                      <div className="text-sm font-semibold mb-1">Assigné à</div>
                      <select className="w-full border rounded px-2 py-1" value={filterAssignee} onChange={e => setFilterAssignee(e.target.value)}>
                        <option value="">Tous</option>
                        {members.map(m => <option key={m.id} value={m.id}>{m.user_full_name || m.user_email}</option>)}
                      </select>
                    </div>
                  </div>
                  <div>
                    <div className="text-sm font-semibold mb-1">Priorité</div>
                    <div className="flex gap-2">
                      {(['', 'low', 'medium', 'high'] as const).map(p => (
                        <Button key={p || 'all'} size="sm" variant={filterPriority === p ? 'default' : 'outline'} onClick={() => setFilterPriority(p as any)}>
                          {p ? (p === 'low' ? 'Faible' : p === 'medium' ? 'Moyenne' : 'Haute') : 'Toutes'}
                        </Button>
                      ))}
                    </div>
                  </div>
                </div>
              )}
            </div>
            <Dialog open={isWizardOpen} onOpenChange={setIsWizardOpen}>
              <DialogTrigger asChild>
                <Button className="bg-blue-600 hover:bg-blue-700 text-white">
                  <Plus className="h-4 w-4 mr-2" />
                  Créer une tâche
                </Button>
              </DialogTrigger>
              <DialogContent className="max-w-2xl">
                <DialogTitle>Nouvelle tâche</DialogTitle>
                {householdId && (
                  <TaskWizard
                    mode="create"
                    householdId={householdId}
                    onSubmit={createTask}
                  />
                )}
              </DialogContent>
            </Dialog>
            <div className="flex bg-white border border-gray-200 rounded-md">
              {(['day', 'week', 'month'] as const).map((viewOption) => (
                <Button
                  key={viewOption}
                  variant={view === viewOption ? 'default' : 'ghost'}
                  size="sm"
                  onClick={() => setView(viewOption)}
                  className={view === viewOption ? 'bg-blue-600 text-white' : 'hover:bg-gray-50'}
                >
                  {viewOption === 'day' ? 'Jour' : viewOption === 'week' ? 'Semaine' : 'Mois'}
                </Button>
              ))}
            </div>
          </div>
        </div>

        <Card className="shadow-sm border-0 bg-white">
          <CardContent className="p-6">
            <div className="flex items-center justify-between mb-6">
              <h2 className="text-xl font-semibold text-gray-900">
                {view === 'month' ? monthLabel : view === 'week' ? weekLabel : dayLabel}
              </h2>
              <div className="flex items-center gap-2">
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => navigateBy(view, 'prev')}
                  className="border-gray-200 hover:bg-gray-50"
                >
                  <ChevronLeft className="h-4 w-4" />
                </Button>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => setCurrentDate(new Date())}
                  className="border-gray-200 hover:bg-gray-50"
                >
                  Aujourd'hui
                </Button>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => navigateBy(view, 'next')}
                  className="border-gray-200 hover:bg-gray-50"
                >
                  <ChevronRight className="h-4 w-4" />
                </Button>
              </div>
            </div>

            {view === 'month' && (
              <div className="grid grid-cols-7 gap-1">
                {dayNames.map((day) => (
                  <div key={day} className="p-2 text-center text-sm font-medium text-gray-600 border-b">
                    {day}
                  </div>
                ))}

                {getDaysGridForMonth(currentDate).map((d, index) => {
                  const key = d ? formatYMD(d) : `empty-${index}`;
                  const list = d ? (occurrencesByDay[key] || []) : [];
                  const isToday = d ? formatYMD(d) === formatYMD(new Date()) : false;
                  return (
                    <div key={key} className={`min-h-[110px] border border-gray-100 p-2 ${isToday ? 'bg-blue-50' : ''}`}>
                      {d && (
                        <>
                          <div className="text-sm font-medium text-gray-900 mb-1 flex items-center justify-between">
                            <span>{d.getDate()}</span>
                            {isToday && <span className="text-xs text-blue-700">Aujourd'hui</span>}
                          </div>
                          <div className="space-y-1">
                            {list.slice(0, 4).map((o) => (
                              <div
                                key={o.id}
                                className="text-xs p-1 rounded bg-gray-50 border-l-2 cursor-pointer hover:bg-gray-100"
                                onClick={() => navigate(`/tasks/${o.task_id}/edit`)}
                                role="button"
                                tabIndex={0}
                                onKeyPress={(e) => { if (e.key === 'Enter') navigate(`/tasks/${o.task_id}/edit`); }}
                              >
                                <div className="flex items-center gap-1">
                                  <div className={`w-2 h-2 rounded-full ${statusColor(o.status)}`} />
                                  <span className="font-medium truncate">{o.definition_title}</span>
                                </div>
                                <div className="text-gray-600 truncate">
                                  {o.room_name || 'Pièce'} • {o.due_at ? fmt({ hour: '2-digit', minute: '2-digit' }).format(new Date(o.due_at)) : '—'}
                                </div>
                              </div>
                            ))}
                            {list.length > 4 && (
                              <div className="text-[11px] text-gray-500">+{list.length - 4} autres</div>
                            )}
                          </div>
                        </>
                      )}
                    </div>
                  );
                })}
              </div>
            )}

            {view === 'day' && (
              <div className="space-y-4">
                <h3 className="text-lg font-semibold text-gray-900">{dayLabel}</h3>
                <div className="space-y-2">
                  {(occurrencesByDay[formatYMD(currentDate)] || []).map((o) => (
                    <Card
                      key={o.id}
                      className="border-l-4 hover:shadow-md transition-shadow cursor-pointer"
                      onClick={() => navigate(`/tasks/${o.task_id}/edit`)}
                      role="button"
                      tabIndex={0}
                      onKeyPress={(e) => { if (e.key === 'Enter') navigate(`/tasks/${o.task_id}/edit`); }}
                    >
                      <CardContent className="p-4">
                        <div className="flex items-center justify-between">
                          <div>
                            <h4 className="font-medium text-gray-900">{o.definition_title}</h4>
                            <p className="text-sm text-gray-600">{o.room_name || 'Pièce'} • {o.due_at ? fmt({ hour: '2-digit', minute: '2-digit' }).format(new Date(o.due_at)) : '—'} • {o.assigned_user_name || 'Non assigné'}</p>
                          </div>
                          <div className="flex items-center gap-2">
                            <Badge
                              variant="secondary"
                              className={
                                o.status === 'done' ? 'bg-green-100 text-green-800 border-green-200' :
                                  o.status === 'overdue' ? 'bg-red-100 text-red-800 border-red-200' :
                                    o.status === 'snoozed' ? 'bg-orange-100 text-orange-800 border-orange-200' :
                                      o.status === 'skipped' ? 'bg-gray-100 text-gray-800 border-gray-200' :
                                        'bg-blue-100 text-blue-800 border-blue-200'
                              }
                            >
                              {o.status}
                            </Badge>
                            {o.status !== 'done' && (
                              <Button size="sm" className="bg-green-600 hover:bg-green-700 text-white" onClick={(e) => { e.stopPropagation(); handleComplete(o.id); }}>
                                <Check className="h-4 w-4 mr-1" />
                                Terminer
                              </Button>
                            )}
                          </div>
                        </div>
                      </CardContent>
                    </Card>
                  ))}
                  {loading && <div className="text-sm text-gray-500">Chargement…</div>}
                  {!loading && (occurrencesByDay[formatYMD(currentDate)] || []).length === 0 && (
                    <div className="text-sm text-gray-500">Aucune tâche pour ce jour.</div>
                  )}
                </div>
              </div>
            )}

            {view === 'week' && (
              <div className="grid md:grid-cols-7 grid-cols-1 gap-2">
                {Array.from({ length: 7 }).map((_, idx) => {
                  const d = new Date(startOfWeek(currentDate));
                  d.setDate(d.getDate() + idx);
                  const key = formatYMD(d);
                  const list = occurrencesByDay[key] || [];
                  const isToday = key === formatYMD(new Date());
                  return (
                    <div key={key} className={`border rounded-md p-2 ${isToday ? 'bg-blue-50' : 'bg-white'}`}>
                      <div className="text-sm font-medium text-gray-900 mb-2 flex items-center justify-between">
                        <span>{fmt({ weekday: 'short', day: '2-digit' }).format(d)}</span>
                        {isToday && <span className="text-xs text-blue-700">Aujourd'hui</span>}
                      </div>
                      <div className="space-y-1">
                        {list.length === 0 && (
                          <div className="text-xs text-gray-500">—</div>
                        )}
                        {list.map(o => (
                          <div
                            key={o.id}
                            className="text-xs p-1 rounded bg-gray-50 border-l-2 cursor-pointer hover:bg-gray-100"
                            onClick={() => navigate(`/tasks/${o.task_id}/edit`)}
                            role="button"
                            tabIndex={0}
                            onKeyPress={(e) => { if (e.key === 'Enter') navigate(`/tasks/${o.task_id}/edit`); }}
                          >
                            <div className="flex items-center gap-1">
                              <div className={`w-2 h-2 rounded-full ${statusColor(o.status)}`} />
                              <span className="font-medium truncate">{o.definition_title}</span>
                            </div>
                            <div className="text-gray-600 truncate">{o.room_name || 'Pièce'} • {o.due_at ? fmt({ hour: '2-digit', minute: '2-digit' }).format(new Date(o.due_at)) : '—'}</div>
                          </div>
                        ))}
                      </div>
                    </div>
                  );
                })}
              </div>
            )}
          </CardContent>
        </Card>
      </main>

      {/* Légende des statuts */}
      <div className="mt-4 text-xs text-gray-600 flex flex-wrap gap-3">
        <div className="flex items-center gap-1"><span className="w-2 h-2 rounded-full bg-blue-500 inline-block" /> À faire</div>
        <div className="flex items-center gap-1"><span className="w-2 h-2 rounded-full bg-green-500 inline-block" /> Terminé</div>
        <div className="flex items-center gap-1"><span className="w-2 h-2 rounded-full bg-red-500 inline-block" /> En retard</div>
        <div className="flex items-center gap-1"><span className="w-2 h-2 rounded-full bg-orange-500 inline-block" /> Reporté</div>
        <div className="flex items-center gap-1"><span className="w-2 h-2 rounded-full bg-gray-400 inline-block" /> Ignoré</div>
      </div>
    </AppLayout>
  );
};

export default Calendar;
