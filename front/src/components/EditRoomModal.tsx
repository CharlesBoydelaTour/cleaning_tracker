import { useEffect, useState } from "react";
import { Dialog, DialogContent, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Loader2 } from "lucide-react";

interface EditRoomModalProps {
    isOpen: boolean;
    onClose: () => void;
    initialName: string;
    onSubmit: (name: string) => void | Promise<void>;
    isLoading?: boolean;
}

const EditRoomModal = ({ isOpen, onClose, initialName, onSubmit, isLoading = false }: EditRoomModalProps) => {
    const [name, setName] = useState(initialName || "");
    const [error, setError] = useState<string | null>(null);

    useEffect(() => {
        if (isOpen) {
            setName(initialName || "");
            setError(null);
        }
    }, [isOpen, initialName]);

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        const trimmed = name.trim();
        if (!trimmed) {
            setError("Le nom est requis");
            return;
        }
        try {
            await onSubmit(trimmed);
            onClose();
        } catch (err: any) {
            const detail = err?.response?.data?.detail || err?.message || "Erreur lors de la mise à jour";
            setError(detail);
        }
    };

    const handleClose = () => {
        setError(null);
        onClose();
    };

    return (
        <Dialog open={isOpen} onOpenChange={handleClose}>
            <DialogContent className="sm:max-w-md">
                <DialogHeader>
                    <DialogTitle>Renommer la pièce</DialogTitle>
                </DialogHeader>
                <form onSubmit={handleSubmit} className="space-y-4">
                    <div className="space-y-2">
                        <Label htmlFor="roomName">Nom de la pièce</Label>
                        <Input
                            id="roomName"
                            placeholder="Ex: Salon"
                            value={name}
                            onChange={(e) => setName(e.target.value)}
                            disabled={isLoading}
                            required
                        />
                        {error && <p className="text-sm text-red-600">{error}</p>}
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
                            disabled={isLoading || !name.trim()}
                        >
                            {isLoading && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
                            Enregistrer
                        </Button>
                    </div>
                </form>
            </DialogContent>
        </Dialog>
    );
};

export default EditRoomModal;
