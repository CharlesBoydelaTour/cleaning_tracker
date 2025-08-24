import React, { useEffect, useMemo, useState } from 'react';
import { Calendar, Clock, Home, Repeat } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Card, CardContent } from '@/components/ui/card';
import { roomsService } from '@/services/rooms.service';
import { membersService } from '@/services/members.service';
import type { Room, HouseholdMember } from '@/types/household.types';

type Mode = 'create' | 'edit';

export interface TaskWizardInitial {
    title?: string;
    description?: string;
    room_id?: string | null;
    estimated_minutes?: number | null;
    assigned_to?: string | null;
    recurrence_rule?: string; // RRULE
    priority?: 'low' | 'medium' | 'high';
    start_date?: string; // YYYY-MM-DD
}

export interface TaskWizardProps {
    mode: Mode;
    householdId: string;
    initial?: TaskWizardInitial;
    onSubmit: (data: {
        title: string;
        description?: string;
        room_id?: string | null;
        estimated_minutes?: number | null;
        assigned_to?: string | null;
        recurrence_rule: string;
        priority?: 'low' | 'medium' | 'high';
        start_date?: string;
    }) => Promise<void>;
    onDeleteDefinition?: () => Promise<void>;
    onReopenToday?: () => Promise<void>;
}

type RecurrenceType = 'once' | 'daily' | 'weekly' | 'monthly';

function parseRRule(rrule?: string): { type: RecurrenceType; weekDays: string[]; monthDays: number[] } {
    const result = { type: 'weekly' as RecurrenceType, weekDays: [] as string[], monthDays: [] as number[] };
    if (!rrule) return result;
    const upper = rrule.toUpperCase();
    if (upper.includes('COUNT=1')) return { type: 'once', weekDays: [], monthDays: [] };
    if (upper.includes('FREQ=DAILY')) return { type: 'daily', weekDays: [], monthDays: [] };
    if (upper.includes('FREQ=MONTHLY')) {
        const m = upper.match(/BYMONTHDAY=([^;]+)/);
        const list = m ? m[1].split(',').map(s => parseInt(s.trim(), 10)).filter(n => Number.isFinite(n)) : [];
        return { type: 'monthly', weekDays: [], monthDays: list };
    }
    if (upper.includes('FREQ=WEEKLY')) {
        const m = upper.match(/BYDAY=([^;]+)/);
        const days = m ? m[1].split(',').map(s => s.trim()).filter(Boolean) : [];
        return { type: 'weekly', weekDays: days, monthDays: [] };
    }
    return result;
}

export const TaskWizard: React.FC<TaskWizardProps> = ({ mode, householdId, initial, onSubmit, onDeleteDefinition, onReopenToday }) => {
    const inEdit = mode === 'edit';
    const [currentStep, setCurrentStep] = useState(inEdit ? 1 : 0);

    // Data
    const [roomsList, setRoomsList] = useState<Room[]>([]);
    const [membersList, setMembersList] = useState<HouseholdMember[]>([]);
    const [loading, setLoading] = useState(false);
    const [errors, setErrors] = useState<Record<string, string>>({});

    // Form
    const parsed = useMemo(() => parseRRule(initial?.recurrence_rule), [initial?.recurrence_rule]);
    const [title, setTitle] = useState(initial?.title || '');
    const [description, setDescription] = useState(initial?.description || '');
    const [roomId, setRoomId] = useState<string>(initial?.room_id || '');
    const [estimated, setEstimated] = useState<number | ''>(initial?.estimated_minutes ?? '');
    const [assignedTo, setAssignedTo] = useState<string>(initial?.assigned_to || 'auto');
    const [recurrenceType, setRecurrenceType] = useState<RecurrenceType>(parsed.type);
    const [recurrenceWeekDays, setRecurrenceWeekDays] = useState<string[]>(parsed.weekDays);
    const [recurrenceMonthDays, setRecurrenceMonthDays] = useState<number[]>(parsed.monthDays);
    const [startDate, setStartDate] = useState<string>(initial?.start_date || new Date().toISOString().split('T')[0]);
    const [priority, setPriority] = useState<'low' | 'medium' | 'high'>(initial?.priority || 'medium');
    // Réagir aux changements de props initial (ex: navigation entre différentes tâches à éditer)
    useEffect(() => {
        if (!initial) return;
        setTitle(initial.title || '');
        setDescription(initial.description || '');
        setRoomId(initial.room_id || '');
        setEstimated(initial.estimated_minutes ?? '');
        setAssignedTo(initial.assigned_to || 'auto');
        setPriority(initial.priority || 'medium');
        setStartDate(initial.start_date || new Date().toISOString().split('T')[0]);
        const p = parseRRule(initial.recurrence_rule);
        setRecurrenceType(p.type);
        setRecurrenceWeekDays(p.weekDays);
        setRecurrenceMonthDays(p.monthDays);
        if (inEdit) setCurrentStep(1);
    }, [initial, inEdit]);

    useEffect(() => {
        const load = async () => {
            try {
                const [r, m] = await Promise.all([
                    roomsService.getAll(householdId),
                    membersService.getAll(householdId)
                ]);
                setRoomsList(r);
                setMembersList(m);
            } catch (e) {
                // Silence: le parent gère les toasts si nécessaire
            }
        };
        if (householdId) load();
    }, [householdId]);

    const DAYS_OF_WEEK = [
        { value: 'MO', label: 'Lun' },
        { value: 'TU', label: 'Mar' },
        { value: 'WE', label: 'Mer' },
        { value: 'TH', label: 'Jeu' },
        { value: 'FR', label: 'Ven' },
        { value: 'SA', label: 'Sam' },
        { value: 'SU', label: 'Dim' }
    ];

    const validateStep = (step: number): boolean => {
        const newErrors: Record<string, string> = {};
        if (step === 1) {
            if (!title.trim()) newErrors.title = 'Le titre est requis';
            const n = typeof estimated === 'number' ? estimated : 0;
            if (n <= 0) newErrors.estimated = 'La durée doit être positive';
        } else if (step === 2) {
            if (!roomId) newErrors.roomId = 'Veuillez sélectionner une pièce';
        } else if (step === 3) {
            if (recurrenceType === 'weekly' && recurrenceWeekDays.length === 0) {
                newErrors.recurrence = 'Sélectionnez au moins un jour de la semaine';
            }
            if (recurrenceType === 'monthly' && recurrenceMonthDays.length === 0) {
                newErrors.recurrence = 'Sélectionnez au moins un jour du mois';
            }
        }
        setErrors(newErrors);
        return Object.keys(newErrors).length === 0;
    };

    const handleWeekDayToggle = (day: string) => {
        setRecurrenceWeekDays(prev => prev.includes(day) ? prev.filter(d => d !== day) : [...prev, day]);
    };

    const handleMonthDayToggle = (d: number) => {
        setRecurrenceMonthDays(prev => prev.includes(d) ? prev.filter(x => x !== d) : [...prev, d].sort((a, b) => a - b));
    };

    // Quand on change de type, on n’efface pas la date de début mais on réinitialise les sélections spécifiques
    useEffect(() => {
        if (recurrenceType === 'weekly' && recurrenceWeekDays.length === 0) {
            // rien, l’utilisateur choisira
        }
        if (recurrenceType === 'monthly' && recurrenceMonthDays.length === 0) {
            // rien, l’utilisateur choisira
        }
    }, [recurrenceType]);

    const buildRRule = (): string => {
        switch (recurrenceType) {
            case 'daily':
                return 'FREQ=DAILY';
            case 'monthly': {
                const md = recurrenceMonthDays.length ? `;BYMONTHDAY=${recurrenceMonthDays.join(',')}` : '';
                return `FREQ=MONTHLY${md}`;
            }
            case 'once':
                // Une seule occurrence à la date de début
                return 'FREQ=DAILY;COUNT=1';
            case 'weekly':
            default: {
                const wd = recurrenceWeekDays.length ? `;BYDAY=${recurrenceWeekDays.join(',')}` : '';
                return `FREQ=WEEKLY${wd}`;
            }
        }
    };

    const submit = async () => {
        if (!validateStep(currentStep)) return;
        setLoading(true);
        try {
            await onSubmit({
                title,
                description: description || undefined,
                room_id: roomId || null,
                estimated_minutes: typeof estimated === 'number' ? estimated : null,
                assigned_to: assignedTo === 'auto' ? null : assignedTo,
                recurrence_rule: buildRRule(),
                priority,
                start_date: startDate
            });
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="space-y-6">
            {/* Progress */}
            <div className="px-0 py-0">
                <div className="flex items-center space-x-4">
                    {(inEdit ? [1, 2, 3] : [0, 1, 2, 3]).map((step, idx) => (
                        <div key={step} className="flex items-center">
                            <div className={`w-8 h-8 rounded-full flex items-center justify-center text-sm font-medium ${step <= currentStep
                                ? 'bg-blue-600 text-white'
                                : 'bg-gray-200 text-gray-600'}`}>
                                {inEdit ? step : step + 1}
                            </div>
                            {idx < (inEdit ? 2 : 3) && (
                                <div className={`w-12 h-1 mx-2 ${step < currentStep ? 'bg-blue-600' : 'bg-gray-200'}`} />
                            )}
                        </div>
                    ))}
                </div>
                <div className="mt-2 text-sm text-gray-600">
                    {currentStep === 0 && !inEdit && 'Choisir un modèle'}
                    {currentStep === 1 && 'Détails de la tâche'}
                    {currentStep === 2 && 'Lieu et assignation'}
                    {currentStep === 3 && 'Récurrence et confirmation'}
                </div>
            </div>

            {/* Steps */}
            {currentStep === 1 && (
                <div className="space-y-4">
                    <div className="space-y-2">
                        <Label>Titre *</Label>
                        <Input value={title} onChange={e => setTitle(e.target.value)} placeholder="Ex: Passer l'aspirateur" />
                        {errors.title && <p className="text-red-600 text-sm">{errors.title}</p>}
                    </div>
                    <div className="space-y-2">
                        <Label>Description</Label>
                        <Textarea value={description} onChange={e => setDescription(e.target.value)} rows={3} />
                    </div>
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                        <div className="space-y-2">
                            <Label>Pièce *</Label>
                            <Select value={roomId} onValueChange={setRoomId}>
                                <SelectTrigger>
                                    <div className="flex items-center gap-2">
                                        <Home className="h-4 w-4 text-gray-400" />
                                        <SelectValue placeholder="Sélectionner une pièce" />
                                    </div>
                                </SelectTrigger>
                                <SelectContent>
                                    {roomsList.map(r => (
                                        <SelectItem key={r.id} value={r.id}>{r.name}</SelectItem>
                                    ))}
                                </SelectContent>
                            </Select>
                            {errors.roomId && <p className="text-red-600 text-sm">{errors.roomId}</p>}
                        </div>
                        <div className="space-y-2">
                            <Label>Durée estimée (minutes)</Label>
                            <div className="relative">
                                <Clock className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-gray-400" />
                                <Input type="number" className="pl-10" value={estimated} onChange={e => setEstimated(parseInt(e.target.value) || '')} min={1} />
                            </div>
                            {errors.estimated && <p className="text-red-600 text-sm">{errors.estimated}</p>}
                        </div>
                    </div>
                </div>
            )}

            {currentStep === 2 && (
                <div className="space-y-4">
                    <div className="space-y-2">
                        <Label>Assigner à</Label>
                        <Select value={assignedTo} onValueChange={setAssignedTo}>
                            <SelectTrigger>
                                <SelectValue placeholder="Sélectionner un membre" />
                            </SelectTrigger>
                            <SelectContent>
                                <SelectItem value="auto">Automatique</SelectItem>
                                {membersList.map(m => (
                                    <SelectItem key={m.id} value={m.id}>{m.user_full_name || m.user_email || 'Membre'}</SelectItem>
                                ))}
                            </SelectContent>
                        </Select>
                    </div>
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                        <div className="space-y-2">
                            <Label>Date de début</Label>
                            <div className="relative">
                                <Calendar className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-gray-400" />
                                <Input type="date" className="pl-10" value={startDate} onChange={e => setStartDate(e.target.value)} />
                            </div>
                        </div>
                        <div className="space-y-2">
                            <Label>Priorité</Label>
                            <Select value={priority} onValueChange={(v: any) => setPriority(v)}>
                                <SelectTrigger>
                                    <SelectValue placeholder="Sélectionner" />
                                </SelectTrigger>
                                <SelectContent>
                                    <SelectItem value="low">Faible</SelectItem>
                                    <SelectItem value="medium">Moyenne</SelectItem>
                                    <SelectItem value="high">Haute</SelectItem>
                                </SelectContent>
                            </Select>
                        </div>
                    </div>
                </div>
            )}

            {currentStep === 3 && (
                <div className="space-y-4">
                    <div className="space-y-2">
                        <Label>Récurrence</Label>
                        <Select value={recurrenceType} onValueChange={(v: any) => setRecurrenceType(v)}>
                            <SelectTrigger>
                                <div className="flex items-center gap-2">
                                    <Repeat className="h-4 w-4 text-gray-400" />
                                    <SelectValue placeholder="Sélectionner une récurrence" />
                                </div>
                            </SelectTrigger>
                            <SelectContent>
                                <SelectItem value="once">Ponctuelle</SelectItem>
                                <SelectItem value="daily">Quotidienne</SelectItem>
                                <SelectItem value="weekly">Hebdomadaire</SelectItem>
                                <SelectItem value="monthly">Mensuelle</SelectItem>
                            </SelectContent>
                        </Select>
                    </div>

                    {recurrenceType === 'weekly' && (
                        <div className="flex flex-wrap gap-2">
                            {DAYS_OF_WEEK.map(d => (
                                <Button key={d.value} type="button" variant={recurrenceWeekDays.includes(d.value) ? 'default' : 'outline'} onClick={() => handleWeekDayToggle(d.value)}>
                                    {d.label}
                                </Button>
                            ))}
                            {errors.recurrence && <p className="text-red-600 text-sm w-full">{errors.recurrence}</p>}
                        </div>
                    )}

                    {recurrenceType === 'monthly' && (
                        <div className="space-y-2">
                            <div className="grid grid-cols-7 gap-2">
                                {Array.from({ length: 31 }, (_, i) => i + 1).map((d) => (
                                    <Button
                                        key={d}
                                        type="button"
                                        variant={recurrenceMonthDays.includes(d) ? 'default' : 'outline'}
                                        onClick={() => handleMonthDayToggle(d)}
                                    >
                                        {d}
                                    </Button>
                                ))}
                            </div>
                            {errors.recurrence && <p className="text-red-600 text-sm">{errors.recurrence}</p>}
                        </div>
                    )}

                    <Card className="bg-blue-50 border-blue-200">
                        <CardContent className="p-4">
                            <h4 className="font-medium text-blue-900 mb-2">Aperçu 30 jours</h4>
                            <p className="text-sm text-blue-700">
                                {recurrenceType === 'once'
                                    ? `Tâche unique le ${startDate}`
                                    : recurrenceType === 'daily'
                                        ? `Tous les jours à partir du ${startDate}`
                                        : recurrenceType === 'weekly'
                                            ? (recurrenceWeekDays.length ? `Chaque ${recurrenceWeekDays.join(', ')} à partir du ${startDate}` : `Hebdomadaire à partir du ${startDate}`)
                                            : recurrenceType === 'monthly'
                                                ? (recurrenceMonthDays.length ? `Chaque mois aux jours ${recurrenceMonthDays.join(', ')} à partir du ${startDate}` : `Mensuelle à partir du ${startDate}`)
                                                : ''}
                            </p>
                        </CardContent>
                    </Card>
                </div>
            )}

            {/* Footer */}
            <div className="flex items-center justify-between pt-2">
                <div className="flex gap-2">
                    {currentStep > (inEdit ? 1 : 0) && (
                        <Button type="button" variant="outline" onClick={() => setCurrentStep(prev => prev - 1)}>Précédent</Button>
                    )}
                </div>
                <div className="flex gap-2 items-center flex-wrap justify-end">
                    {inEdit && (
                        <>
                            {onReopenToday && (
                                <Button type="button" variant="outline" onClick={onReopenToday}>
                                    Remettre à aujourd'hui
                                </Button>
                            )}
                            {onDeleteDefinition && (
                                <Button type="button" variant="destructive" onClick={onDeleteDefinition}>
                                    Supprimer la tâche
                                </Button>
                            )}
                        </>
                    )}
                    {currentStep < 3 ? (
                        <Button type="button" onClick={() => {
                            if (validateStep(currentStep)) setCurrentStep(prev => prev + 1);
                        }}>Suivant</Button>
                    ) : (
                        <Button type="button" disabled={loading} onClick={submit}>{loading ? 'Envoi...' : (inEdit ? 'Mettre à jour' : 'Créer')}</Button>
                    )}
                </div>
            </div>
        </div>
    );
};

export default TaskWizard;
