import { useState } from "react";
import { Dialog, DialogContent, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Loader2, Mail } from "lucide-react";

interface InviteMemberModalProps {
    isOpen: boolean;
    onClose: () => void;
    onSubmit: (data: { email: string; role: 'admin' | 'member' | 'guest' }) => void;
    isLoading?: boolean;
}

const InviteMemberModal = ({ isOpen, onClose, onSubmit, isLoading = false }: InviteMemberModalProps) => {
    const [formData, setFormData] = useState({
        email: '',
        role: 'member' as 'admin' | 'member' | 'guest'
    });

    const handleSubmit = (e: React.FormEvent) => {
        e.preventDefault();
        if (!formData.email.trim()) return;

        onSubmit({
            email: formData.email.trim(),
            role: formData.role
        });
    };

    const handleClose = () => {
        setFormData({ email: '', role: 'member' });
        onClose();
    };

    const roleLabels = {
        admin: 'Administrateur',
        member: 'Membre',
        guest: 'Invité'
    };

    const roleDescriptions = {
        admin: 'Peut gérer tous les aspects du foyer',
        member: 'Peut créer et gérer les tâches',
        guest: 'Accès en lecture seule'
    };

    return (
        <Dialog open={isOpen} onOpenChange={handleClose}>
            <DialogContent className="sm:max-w-md">
                <DialogHeader>
                    <DialogTitle className="flex items-center gap-2">
                        <Mail className="h-5 w-5" />
                        Inviter un nouveau membre
                    </DialogTitle>
                </DialogHeader>
                <form onSubmit={handleSubmit} className="space-y-4">
                    <div className="space-y-2">
                        <Label htmlFor="memberEmail">Adresse email</Label>
                        <Input
                            id="memberEmail"
                            type="email"
                            placeholder="exemple@email.com"
                            value={formData.email}
                            onChange={(e) => setFormData({ ...formData, email: e.target.value })}
                            disabled={isLoading}
                            required
                        />
                    </div>

                    <div className="space-y-2">
                        <Label htmlFor="memberRole">Rôle</Label>
                        <Select
                            value={formData.role}
                            onValueChange={(role: 'admin' | 'member' | 'guest') =>
                                setFormData({ ...formData, role })
                            }
                            disabled={isLoading}
                        >
                            <SelectTrigger>
                                <SelectValue />
                            </SelectTrigger>
                            <SelectContent>
                                {Object.entries(roleLabels).map(([value, label]) => (
                                    <SelectItem key={value} value={value}>
                                        <div className="flex flex-col items-start">
                                            <span className="font-medium">{label}</span>
                                            <span className="text-xs text-gray-500">
                                                {roleDescriptions[value as keyof typeof roleDescriptions]}
                                            </span>
                                        </div>
                                    </SelectItem>
                                ))}
                            </SelectContent>
                        </Select>
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
                            disabled={isLoading || !formData.email.trim()}
                        >
                            {isLoading && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
                            Envoyer l'invitation
                        </Button>
                    </div>
                </form>
            </DialogContent>
        </Dialog>
    );
};

export default InviteMemberModal;
