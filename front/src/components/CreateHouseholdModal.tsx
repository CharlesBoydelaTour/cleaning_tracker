import { useState } from 'react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import {
    Dialog,
    DialogContent,
    DialogDescription,
    DialogHeader,
    DialogTitle,
} from '@/components/ui/dialog';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Home, Users, Sparkles, AlertCircle } from 'lucide-react';
import { householdsService } from '@/services/households.service';

interface CreateHouseholdModalProps {
    open: boolean;
    onOpenChange: (open: boolean) => void;
    onSuccess: () => void;
}

const CreateHouseholdModal = ({ open, onOpenChange, onSuccess }: CreateHouseholdModalProps) => {
    const [householdName, setHouseholdName] = useState('');
    const [isLoading, setIsLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();

        if (!householdName.trim()) {
            setError('Le nom du ménage est requis');
            return;
        }

        setIsLoading(true);
        setError(null);

        try {
            await householdsService.create({ name: householdName.trim() });
            setHouseholdName('');
            onSuccess();
            onOpenChange(false);
        } catch (err) {
            console.error('Erreur lors de la création du ménage:', err);
            setError(err instanceof Error ? err.message : 'Erreur lors de la création du ménage');
        } finally {
            setIsLoading(false);
        }
    };

    const resetForm = () => {
        setHouseholdName('');
        setError(null);
    };

    return (
        <Dialog open={open} onOpenChange={(open) => {
            if (!open) resetForm();
            onOpenChange(open);
        }}>
            <DialogContent className="sm:max-w-[500px]">
                <DialogHeader>
                    <DialogTitle className="text-2xl font-bold text-gray-900 flex items-center gap-2">
                        <Home className="h-6 w-6 text-blue-600" />
                        Créer votre ménage
                    </DialogTitle>
                    <DialogDescription className="text-gray-600">
                        Commencez par créer votre premier ménage pour organiser les tâches ménagères.
                    </DialogDescription>
                </DialogHeader>

                <div className="space-y-6">
                    {/* Features highlight */}
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                        <Card className="bg-blue-50 border-blue-200">
                            <CardContent className="p-4">
                                <div className="flex items-center gap-2 mb-2">
                                    <Users className="h-4 w-4 text-blue-600" />
                                    <span className="text-sm font-medium text-blue-900">Collaboration</span>
                                </div>
                                <p className="text-xs text-blue-700">
                                    Invitez famille et colocataires
                                </p>
                            </CardContent>
                        </Card>

                        <Card className="bg-green-50 border-green-200">
                            <CardContent className="p-4">
                                <div className="flex items-center gap-2 mb-2">
                                    <Sparkles className="h-4 w-4 text-green-600" />
                                    <span className="text-sm font-medium text-green-900">Organisation</span>
                                </div>
                                <p className="text-xs text-green-700">
                                    Planifiez et suivez les tâches
                                </p>
                            </CardContent>
                        </Card>
                    </div>

                    {/* Form */}
                    <form onSubmit={handleSubmit} className="space-y-4">
                        <div className="space-y-2">
                            <Label htmlFor="householdName" className="text-sm font-medium text-gray-700">
                                Nom du ménage
                            </Label>
                            <Input
                                id="householdName"
                                type="text"
                                placeholder="Ex: Famille Dupont, Colocation Centre-ville..."
                                value={householdName}
                                onChange={(e) => setHouseholdName(e.target.value)}
                                className="w-full"
                                maxLength={100}
                                disabled={isLoading}
                            />
                        </div>

                        {error && (
                            <div className="flex items-center gap-2 p-3 bg-red-50 border border-red-200 rounded-md">
                                <AlertCircle className="h-4 w-4 text-red-600 flex-shrink-0" />
                                <span className="text-sm text-red-700">{error}</span>
                            </div>
                        )}

                        <div className="flex gap-3 pt-4">
                            <Button
                                type="button"
                                variant="outline"
                                onClick={() => onOpenChange(false)}
                                disabled={isLoading}
                                className="flex-1"
                            >
                                Annuler
                            </Button>
                            <Button
                                type="submit"
                                disabled={isLoading || !householdName.trim()}
                                className="flex-1 bg-blue-600 hover:bg-blue-700"
                            >
                                {isLoading ? (
                                    <div className="flex items-center gap-2">
                                        <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
                                        Création...
                                    </div>
                                ) : (
                                    'Créer le ménage'
                                )}
                            </Button>
                        </div>
                    </form>
                </div>
            </DialogContent>
        </Dialog>
    );
};

export default CreateHouseholdModal;
