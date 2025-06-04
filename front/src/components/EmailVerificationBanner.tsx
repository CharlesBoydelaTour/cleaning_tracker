import { useState, useEffect } from 'react';
import { Mail, X } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { useAuth } from '@/contexts/AuthContext';
import { authService } from '@/services/auth.service';
import { useToast } from '@/hooks/use-toast';

export function EmailVerificationBanner() {
    const { user } = useAuth();
    const { toast } = useToast();
    const [isVisible, setIsVisible] = useState(false);
    const [isSending, setIsSending] = useState(false);

    useEffect(() => {
        // Afficher seulement si l'email n'est pas confirmé
        if (user && !user.email_confirmed_at) {
            setIsVisible(true);
        } else {
            setIsVisible(false);
        }
    }, [user]);

    const handleResendEmail = async () => {
        if (!user?.email) return;

        setIsSending(true);
        try {
            await authService.resendVerificationEmail(user.email);
            toast({
                title: "Email envoyé",
                description: "Un nouvel email de vérification a été envoyé.",
            });
        } catch (error) {
            toast({
                title: "Erreur",
                description: "Impossible d'envoyer l'email de vérification.",
                variant: "destructive",
            });
        } finally {
            setIsSending(false);
        }
    };

    if (!isVisible) return null;

    return (
        <Alert className="bg-yellow-50 border-yellow-200 mb-4">
            <Mail className="h-4 w-4 text-yellow-600" />
            <AlertDescription className="flex items-center justify-between">
                <span className="text-yellow-800">
                    Votre adresse email n'est pas encore vérifiée. Vérifiez votre boîte de réception.
                </span>
                <div className="flex items-center gap-2">
                    <Button
                        variant="ghost"
                        size="sm"
                        onClick={handleResendEmail}
                        disabled={isSending}
                        className="text-yellow-700 hover:text-yellow-800 hover:bg-yellow-100"
                    >
                        {isSending ? 'Envoi...' : 'Renvoyer'}
                    </Button>
                    <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => setIsVisible(false)}
                        className="text-yellow-700 hover:text-yellow-800 hover:bg-yellow-100 p-1"
                    >
                        <X className="h-4 w-4" />
                    </Button>
                </div>
            </AlertDescription>
        </Alert>
    );
}