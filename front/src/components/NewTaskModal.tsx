import React, { useState, useEffect } from 'react';
import { X, Calendar, Clock, User, Home, Repeat, Plus } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';

interface NewTaskModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSubmit: (taskData: any) => Promise<void>;
  householdId: string;
}

interface TaskFormData {
  title: string;
  description: string;
  room_id: string;
  estimated_minutes: number;
  assigned_to: string;
  recurrence_type: 'once' | 'daily' | 'weekly' | 'monthly';
  recurrence_days: string[];
  start_date: string;
  priority: 'low' | 'medium' | 'high';
}

const DAYS_OF_WEEK = [
  { value: 'MO', label: 'Lun' },
  { value: 'TU', label: 'Mar' },
  { value: 'WE', label: 'Mer' },
  { value: 'TH', label: 'Jeu' },
  { value: 'FR', label: 'Ven' },
  { value: 'SA', label: 'Sam' },
  { value: 'SU', label: 'Dim' }
];

const TASK_TEMPLATES = [
  { title: 'Faire la vaisselle', description: 'Laver et ranger la vaisselle', room: 'Cuisine', duration: 15, icon: '🍽️' },
  { title: 'Passer l\'aspirateur', description: 'Aspirer les sols', room: 'Salon', duration: 30, icon: '🧹' },
  { title: 'Nettoyer la salle de bain', description: 'Nettoyer lavabo, douche et toilettes', room: 'Salle de bain', duration: 45, icon: '🚿' },
  { title: 'Faire les lits', description: 'Refaire tous les lits', room: 'Chambre', duration: 10, icon: '🛏️' },
  { title: 'Sortir les poubelles', description: 'Vider et sortir les poubelles', room: 'Cuisine', duration: 5, icon: '🗑️' },
];

export const NewTaskModal: React.FC<NewTaskModalProps> = ({
  isOpen,
  onClose,
  onSubmit,
  householdId
}) => {
  const [currentStep, setCurrentStep] = useState(0);
  const [formData, setFormData] = useState<TaskFormData>({
    title: '',
    description: '',
    room_id: '',
    estimated_minutes: 30,
    assigned_to: 'auto', // ✅ Valeur par défaut non-vide
    recurrence_type: 'weekly',
    recurrence_days: [],
    start_date: new Date().toISOString().split('T')[0],
    priority: 'medium'
  });
  const [loading, setLoading] = useState(false);
  const [errors, setErrors] = useState<Record<string, string>>({});
  const [isSuccess, setIsSuccess] = useState(false);

  // Mock data - à remplacer par de vraies données de l'API
  const rooms = [
    { id: 'kitchen', name: 'Cuisine' },
    { id: 'living-room', name: 'Salon' },
    { id: 'bathroom', name: 'Salle de bain' },
    { id: 'bedroom', name: 'Chambre' },
    { id: 'office', name: 'Bureau' }
  ];

  const members = [
    { id: 'user1', name: 'Moi', email: 'me@example.com' },
    { id: 'user2', name: 'Marie Dupont', email: 'marie@example.com' },
    { id: 'user3', name: 'Jean Martin', email: 'jean@example.com' }
  ];

  useEffect(() => {
    if (isOpen) {
      setCurrentStep(0);
      setErrors({});
      setFormData({
        title: '',
        description: '',
        room_id: '',
        estimated_minutes: 30,
        assigned_to: 'auto', // ✅ Valeur par défaut non-vide
        recurrence_type: 'weekly',
        recurrence_days: [],
        start_date: new Date().toISOString().split('T')[0],
        priority: 'medium'
      });
    }
  }, [isOpen]);

  const handleInputChange = (field: keyof TaskFormData, value: any) => {
    setFormData(prev => ({ ...prev, [field]: value }));
    // Clear error when user starts typing
    if (errors[field]) {
      setErrors(prev => ({ ...prev, [field]: '' }));
    }
  };

  const handleTemplateSelect = (template: typeof TASK_TEMPLATES[0]) => {
    setFormData(prev => ({
      ...prev,
      title: template.title,
      description: template.description,
      estimated_minutes: template.duration,
      room_id: rooms.find(r => r.name === template.room)?.id || ''
    }));
    setCurrentStep(1);
  };

  const handleDayToggle = (day: string) => {
    setFormData(prev => ({
      ...prev,
      recurrence_days: prev.recurrence_days.includes(day)
        ? prev.recurrence_days.filter(d => d !== day)
        : [...prev.recurrence_days, day]
    }));
  };

  const validateStep = (step: number): boolean => {
    const newErrors: Record<string, string> = {};

    switch (step) {
      case 1: // Détails de la tâche
        if (!formData.title.trim()) newErrors.title = 'Le titre est requis';
        if (formData.estimated_minutes <= 0) newErrors.estimated_minutes = 'La durée doit être positive';
        break;
      case 2: // Lieu et assignation
        if (!formData.room_id) newErrors.room_id = 'Veuillez sélectionner une pièce';
        break;
      case 3: // Récurrence
        if (formData.recurrence_type === 'weekly' && formData.recurrence_days.length === 0) {
          newErrors.recurrence_days = 'Sélectionnez au moins un jour';
        }
        break;
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleNext = () => {
    console.log('Current step:', currentStep);
    console.log('Form data:', formData);

    if (currentStep === 0) {
      // Step 0 (template selection) - no validation needed, just go to next step
      setCurrentStep(1);
      return;
    }

    if (validateStep(currentStep)) {
      setCurrentStep(prev => Math.min(prev + 1, 3));
    } else {
      console.log('Validation failed, errors:', errors);
    }
  };

  const handlePrevious = () => {
    setCurrentStep(prev => Math.max(prev - 1, 0));
  };

  const handleSubmit = async () => {
    if (!validateStep(currentStep)) return;

    setLoading(true);
    setIsSuccess(false);

    try {
      // Construire la règle de récurrence RRULE
      let rrule = '';
      switch (formData.recurrence_type) {
        case 'daily':
          rrule = 'FREQ=DAILY';
          break;
        case 'weekly':
          rrule = `FREQ=WEEKLY;BYDAY=${formData.recurrence_days.join(',')}`;
          break;
        case 'monthly':
          rrule = 'FREQ=MONTHLY';
          break;
        case 'once':
          rrule = '';
          break;
      }

      const taskData = {
        title: formData.title,
        description: formData.description,
        room_id: formData.room_id,
        estimated_minutes: formData.estimated_minutes,
        assigned_to: formData.assigned_to === 'auto' ? null : formData.assigned_to, // ✅ Convertir 'auto' en null
        recurrence_rule: rrule,
        priority: formData.priority,
        start_date: formData.start_date
      };

      console.log('Submitting task data:', taskData);

      // Attendre que la soumission soit terminée avant de fermer
      await onSubmit(taskData);

      console.log('Tâche créée avec succès');
      setIsSuccess(true);

      // Petit délai pour montrer le succès puis fermer
      setTimeout(() => {
        onClose();
        setIsSuccess(false);
      }, 1000);

    } catch (error) {
      console.error('Erreur lors de la création de la tâche:', error);
      alert('Erreur lors de la création de la tâche. Veuillez réessayer.');
    } finally {
      setLoading(false);
    }
  };

  const generateRecurrencePreview = () => {
    if (formData.recurrence_type === 'once') return 'Tâche unique';
    if (formData.recurrence_type === 'daily') return 'Tous les jours';
    if (formData.recurrence_type === 'monthly') return 'Tous les mois';
    if (formData.recurrence_type === 'weekly' && formData.recurrence_days.length > 0) {
      const dayLabels = formData.recurrence_days.map(day =>
        DAYS_OF_WEEK.find(d => d.value === day)?.label
      ).join(', ');
      return `Chaque ${dayLabels}`;
    }
    return 'Non définie';
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-lg shadow-xl w-full max-w-2xl max-h-[90vh] overflow-hidden">
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b">
          <h2 className="text-xl font-semibold text-gray-900">
            Nouvelle tâche
          </h2>
          <Button variant="ghost" size="icon" onClick={onClose}>
            <X className="h-5 w-5" />
          </Button>
        </div>

        {/* Progress indicator */}
        <div className="px-6 py-4 border-b bg-gray-50">
          <div className="flex items-center space-x-4">
            {[0, 1, 2, 3].map((step) => (
              <div key={step} className="flex items-center">
                <div className={`w-8 h-8 rounded-full flex items-center justify-center text-sm font-medium ${step <= currentStep
                  ? 'bg-blue-600 text-white'
                  : 'bg-gray-200 text-gray-600'
                  }`}>
                  {step + 1}
                </div>
                {step < 3 && (
                  <div className={`w-12 h-1 mx-2 ${step < currentStep ? 'bg-blue-600' : 'bg-gray-200'
                    }`} />
                )}
              </div>
            ))}
          </div>
          <div className="mt-2 text-sm text-gray-600">
            {currentStep === 0 && 'Choisir un modèle'}
            {currentStep === 1 && 'Détails de la tâche'}
            {currentStep === 2 && 'Lieu et assignation'}
            {currentStep === 3 && 'Récurrence et confirmation'}
          </div>
        </div>

        {/* Content */}
        <div className="p-6 overflow-y-auto max-h-[60vh]">
          {/* Step 0: Template Selection */}
          {currentStep === 0 && (
            <div className="space-y-4">
              <div className="text-center mb-6">
                <h3 className="text-lg font-medium text-gray-900 mb-2">
                  Choisissez un modèle de tâche
                </h3>
                <p className="text-gray-600">
                  Sélectionnez un modèle prédéfini ou créez une tâche personnalisée
                </p>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {TASK_TEMPLATES.map((template, index) => (
                  <Card
                    key={index}
                    className="cursor-pointer hover:shadow-md transition-shadow border-2 hover:border-blue-300"
                    onClick={() => handleTemplateSelect(template)}
                  >
                    <CardContent className="p-4">
                      <div className="flex items-start space-x-3">
                        <span className="text-2xl">{template.icon}</span>
                        <div className="flex-1 min-w-0">
                          <h4 className="font-medium text-gray-900 truncate">
                            {template.title}
                          </h4>
                          <p className="text-sm text-gray-600 line-clamp-2">
                            {template.description}
                          </p>
                          <div className="flex items-center mt-2 space-x-3 text-xs text-gray-500">
                            <span className="flex items-center">
                              <Clock className="w-3 h-3 mr-1" />
                              {template.duration} min
                            </span>
                            <span className="flex items-center">
                              <Home className="w-3 h-3 mr-1" />
                              {template.room}
                            </span>
                          </div>
                        </div>
                      </div>
                    </CardContent>
                  </Card>
                ))}
              </div>

              <div className="pt-4 border-t">
                <Button
                  variant="outline"
                  className="w-full"
                  onClick={() => setCurrentStep(1)}
                >
                  <Plus className="w-4 h-4 mr-2" />
                  Créer une tâche personnalisée
                </Button>
              </div>
            </div>
          )}

          {/* Step 1: Task Details */}
          {currentStep === 1 && (
            <div className="space-y-6">
              <div>
                <Label htmlFor="title">Titre de la tâche *</Label>
                <Input
                  id="title"
                  value={formData.title}
                  onChange={(e) => handleInputChange('title', e.target.value)}
                  placeholder="Ex: Faire la vaisselle"
                  className={errors.title ? 'border-red-500' : ''}
                />
                {errors.title && <p className="text-sm text-red-600 mt-1">{errors.title}</p>}
              </div>

              <div>
                <Label htmlFor="description">Description</Label>
                <Textarea
                  id="description"
                  value={formData.description}
                  onChange={(e) => handleInputChange('description', e.target.value)}
                  placeholder="Décrivez la tâche en détail..."
                  rows={3}
                />
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <Label htmlFor="duration">Durée estimée (minutes) *</Label>
                  <Input
                    id="duration"
                    type="number"
                    value={formData.estimated_minutes}
                    onChange={(e) => handleInputChange('estimated_minutes', parseInt(e.target.value) || 0)}
                    min="1"
                    className={errors.estimated_minutes ? 'border-red-500' : ''}
                  />
                  {errors.estimated_minutes && <p className="text-sm text-red-600 mt-1">{errors.estimated_minutes}</p>}
                </div>

                <div>
                  <Label htmlFor="priority">Priorité</Label>
                  <Select value={formData.priority} onValueChange={(value) => handleInputChange('priority', value)}>
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="low">
                        <div className="flex items-center">
                          <div className="w-2 h-2 bg-green-500 rounded-full mr-2"></div>
                          Faible
                        </div>
                      </SelectItem>
                      <SelectItem value="medium">
                        <div className="flex items-center">
                          <div className="w-2 h-2 bg-yellow-500 rounded-full mr-2"></div>
                          Moyenne
                        </div>
                      </SelectItem>
                      <SelectItem value="high">
                        <div className="flex items-center">
                          <div className="w-2 h-2 bg-red-500 rounded-full mr-2"></div>
                          Haute
                        </div>
                      </SelectItem>
                    </SelectContent>
                  </Select>
                </div>
              </div>
            </div>
          )}

          {/* Step 2: Room and Assignment */}
          {currentStep === 2 && (
            <div className="space-y-6">
              <div>
                <Label>Pièce *</Label>
                <div className="grid grid-cols-2 md:grid-cols-3 gap-3 mt-2">
                  {rooms.map((room) => (
                    <Card
                      key={room.id}
                      className={`cursor-pointer transition-all ${formData.room_id === room.id
                        ? 'border-blue-500 bg-blue-50'
                        : 'hover:border-gray-300'
                        } ${errors.room_id ? 'border-red-500' : ''}`}
                      onClick={() => handleInputChange('room_id', room.id)}
                    >
                      <CardContent className="p-3 text-center">
                        <Home className="w-6 h-6 mx-auto mb-2 text-gray-600" />
                        <span className="text-sm font-medium">{room.name}</span>
                      </CardContent>
                    </Card>
                  ))}
                </div>
                {errors.room_id && <p className="text-sm text-red-600 mt-1">{errors.room_id}</p>}
              </div>

              <div>
                <Label>Assigner à</Label>
                <Select
                  value={formData.assigned_to}
                  onValueChange={(value) => handleInputChange('assigned_to', value === 'auto' ? '' : value)}
                >
                  <SelectTrigger>
                    <SelectValue placeholder="Sélectionner un membre (optionnel)" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="auto">Assignation automatique</SelectItem>
                    {members.map((member) => (
                      <SelectItem key={member.id} value={member.id}>
                        <div className="flex items-center">
                          <User className="w-4 h-4 mr-2" />
                          {member.name}
                        </div>
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
            </div>
          )}

          {/* Step 3: Recurrence and Confirmation */}
          {currentStep === 3 && (
            <div className="space-y-6">
              <div>
                <Label>Type de récurrence</Label>
                <div className="grid grid-cols-2 md:grid-cols-4 gap-2 mt-2">
                  {[
                    { value: 'once', label: 'Une fois' },
                    { value: 'daily', label: 'Quotidien' },
                    { value: 'weekly', label: 'Hebdomadaire' },
                    { value: 'monthly', label: 'Mensuel' }
                  ].map((option) => (
                    <Button
                      key={option.value}
                      variant={formData.recurrence_type === option.value ? "default" : "outline"}
                      size="sm"
                      onClick={() => handleInputChange('recurrence_type', option.value)}
                      type="button"
                      className="w-full"
                    >
                      {option.label}
                    </Button>
                  ))}
                </div>
              </div>

              {formData.recurrence_type === 'weekly' && (
                <div>
                  <Label>Jours de la semaine</Label>
                  <div className="flex flex-wrap gap-2 mt-2">
                    {DAYS_OF_WEEK.map((day) => (
                      <Button
                        key={day.value}
                        variant={formData.recurrence_days.includes(day.value) ? "default" : "outline"}
                        size="sm"
                        onClick={() => handleDayToggle(day.value)}
                        type="button"
                      >
                        {day.label}
                      </Button>
                    ))}
                  </div>
                  {errors.recurrence_days && <p className="text-sm text-red-600 mt-1">{errors.recurrence_days}</p>}
                </div>
              )}

              <div>
                <Label htmlFor="start_date">Date de début</Label>
                <Input
                  id="start_date"
                  type="date"
                  value={formData.start_date}
                  onChange={(e) => handleInputChange('start_date', e.target.value)}
                />
              </div>

              {/* Preview */}
              <Card className="bg-gray-50">
                <CardHeader>
                  <CardTitle className="text-lg">Aperçu de la tâche</CardTitle>
                </CardHeader>
                <CardContent className="space-y-3">
                  <div className="flex justify-between">
                    <span className="font-medium">{formData.title}</span>
                    <Badge variant={formData.priority === 'high' ? 'destructive' : formData.priority === 'medium' ? 'default' : 'secondary'}>
                      {formData.priority === 'high' ? 'Haute' : formData.priority === 'medium' ? 'Moyenne' : 'Faible'}
                    </Badge>
                  </div>
                  {formData.description && (
                    <p className="text-sm text-gray-600">{formData.description}</p>
                  )}
                  <div className="flex items-center space-x-4 text-sm text-gray-600">
                    <span className="flex items-center">
                      <Clock className="w-4 h-4 mr-1" />
                      {formData.estimated_minutes} min
                    </span>
                    <span className="flex items-center">
                      <Home className="w-4 h-4 mr-1" />
                      {rooms.find(r => r.id === formData.room_id)?.name}
                    </span>
                    <span className="flex items-center">
                      <Repeat className="w-4 h-4 mr-1" />
                      {generateRecurrencePreview()}
                    </span>
                  </div>
                </CardContent>
              </Card>
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="flex items-center justify-between p-6 border-t bg-gray-50">
          <Button
            variant="outline"
            onClick={currentStep === 0 ? onClose : handlePrevious}
            disabled={loading}
          >
            {currentStep === 0 ? 'Annuler' : 'Précédent'}
          </Button>

          <div className="flex space-x-2">
            {currentStep < 3 ? (
              <Button onClick={handleNext} disabled={loading}>
                Suivant
              </Button>
            ) : (
              <Button onClick={handleSubmit} disabled={loading}>
                {loading ? 'Création...' :
                  isSuccess ? '✅ Créée !' :
                    'Créer la tâche'}
              </Button>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default NewTaskModal;