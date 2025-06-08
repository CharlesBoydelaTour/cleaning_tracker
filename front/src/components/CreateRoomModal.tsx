import { useState } from "react";
import { Dialog, DialogContent, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Loader2 } from "lucide-react";

interface CreateRoomModalProps {
    isOpen: boolean;
    onClose: () => void;
    onSubmit: (roomData: { name: string; icon?: string }) => void;
    isLoading?: boolean;
}

const CreateRoomModal = ({ isOpen, onClose, onSubmit, isLoading = false }: CreateRoomModalProps) => {
    const [formData, setFormData] = useState({
        name: '',
        icon: ''
    });

    const handleSubmit = (e: React.FormEvent) => {
        e.preventDefault();
        if (!formData.name.trim()) return;

        onSubmit({
            name: formData.name.trim(),
            icon: formData.icon.trim() || undefined
        });
    };

    const handleClose = () => {
        setFormData({ name: '', icon: '' });
        onClose();
    };

    // Suggestions d'icônes communes
    const commonIcons = ['🍳', '🛋️', '🛏️', '🚿', '🚽', '💻', '🚗', '🌿', '🏠', '🧺', '🚪'];

    return (
        <Dialog open={isOpen} onOpenChange={handleClose}>
            <DialogContent className="sm:max-w-md">
                <DialogHeader>
                    <DialogTitle>Ajouter une nouvelle pièce</DialogTitle>
                </DialogHeader>
                <form onSubmit={handleSubmit} className="space-y-4">
                    <div className="space-y-2">
                        <Label htmlFor="roomName">Nom de la pièce</Label>
                        <Input
                            id="roomName"
                            placeholder="Ex: Cuisine, Salon, Chambre..."
                            value={formData.name}
                            onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                            disabled={isLoading}
                            required
                        />
                    </div>

                    <div className="space-y-2">
                        <Label htmlFor="roomIcon">Icône (optionnel)</Label>
                        <Input
                            id="roomIcon"
                            placeholder="Ex: 🍳"
                            value={formData.icon}
                            onChange={(e) => setFormData({ ...formData, icon: e.target.value })}
                            disabled={isLoading}
                            maxLength={2}
                        />
                        <div className="flex flex-wrap gap-2">
                            <span className="text-sm text-gray-600 w-full">Suggestions :</span>
                            {commonIcons.map((icon) => (
                                <button
                                    key={icon}
                                    type="button"
                                    className="text-lg hover:bg-gray-100 p-1 rounded"
                                    onClick={() => setFormData({ ...formData, icon })}
                                    disabled={isLoading}
                                >
                                    {icon}
                                </button>
                            ))}
                        </div>
                    </div>

                    <div className="flex justify-end gap-2 pt-4">
                        <Button
                            type="button"
                            variant="outline"
                            onClick={handleClose}
                            disabled={isLoading}
                        >
                            Annuler
                        </Button>
                        <Button
                            type="submit"
                            disabled={isLoading || !formData.name.trim()}
                        >
                            {isLoading && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
                            Créer la pièce
                        </Button>
                    </div>
                </form>
            </DialogContent>
        </Dialog>
    );
};

export default CreateRoomModal;
