
import React, { useEffect, useState } from 'react';
import { User, Mail, Lock, Bell, Trash2, Save } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Switch } from '@/components/ui/switch';
import { useToast } from '@/hooks/use-toast';
import AppLayout from '@/components/AppLayout';
import { AlertDialog, AlertDialogAction, AlertDialogCancel, AlertDialogContent, AlertDialogDescription, AlertDialogFooter, AlertDialogHeader, AlertDialogTitle, AlertDialogTrigger } from '@/components/ui/alert-dialog';
import { authService } from '@/services/auth.service';
import { useAuth } from '@/contexts/AuthContext';
import { useNavigate } from 'react-router-dom';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { invitesService, type UserInvite } from '@/services/invites.service';
import { useCurrentHousehold } from '@/hooks/use-current-household';

const Profile = () => {
  const { toast } = useToast();
  const { user, refreshUser, logout } = useAuth();
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const { householdName, refetch: refetchHousehold } = useCurrentHousehold();
  const [isDeleting, setIsDeleting] = useState(false);
  const [activeHousehold] = useState<string | undefined>(undefined);
  const [profile, setProfile] = useState({
    name: '',
    email: ''
  });

  const [notifications, setNotifications] = useState({
    pushEnabled: true,
    emailEnabled: true,
    reminderTime: 60,
    quietHoursStart: '22:00',
    quietHoursEnd: '07:00'
  });

  const [isLoading, setIsLoading] = useState(false);
  const [pwd, setPwd] = useState({ current: '', next: '', confirm: '' });

  useEffect(() => {
    if (user) {
      setProfile({ name: user.full_name || '', email: user.email || '' });
    } else {
      // Fallback: tenter de charger /auth/me
      authService.getCurrentUser().then(u => {
        setProfile({ name: u.full_name || '', email: u.email || '' });
      }).catch(() => {/* ignore */ });
    }
  }, [user]);

  // Invites: list + actions
  const { data: invites = [], isLoading: invitesLoading, isError: invitesError, refetch: refetchInvites } = useQuery<UserInvite[]>({
    queryKey: ['my-invites'],
    queryFn: invitesService.listMine,
  });

  const acceptInviteMutation = useMutation({
    mutationFn: (inviteId: string) => invitesService.accept(inviteId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['my-invites'] });
      // Mettre à jour le foyer courant et listes associées
      refetchHousehold();
      toast({ title: 'Invitation acceptée', description: 'Vous avez rejoint le foyer.' });
    },
    onError: (error: any) => {
      const detail = error?.response?.data?.detail || error?.message;
      toast({ title: 'Erreur', description: detail || "Impossible d'accepter l'invitation.", variant: 'destructive' });
    }
  });

  const declineInviteMutation = useMutation({
    mutationFn: (inviteId: string) => invitesService.decline(inviteId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['my-invites'] });
      toast({ title: 'Invitation déclinée', description: "L'invitation a été retirée." });
    },
    onError: (error: any) => {
      const detail = error?.response?.data?.detail || error?.message;
      toast({ title: 'Erreur', description: detail || "Impossible de refuser l'invitation.", variant: 'destructive' });
    }
  });

  const handleProfileUpdate = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsLoading(true);
    try {
      await authService.updateProfile({ full_name: profile.name, email: profile.email });
      await refreshUser();
      toast({ title: 'Profil mis à jour', description: 'Vos informations ont été enregistrées.' });
    } catch (err: any) {
      toast({ title: 'Erreur', description: err?.response?.data?.detail || 'Échec de la mise à jour.', variant: 'destructive' });
    } finally {
      setIsLoading(false);
    }
  };

  const handleNotificationUpdate = async () => {
    try {
      // TODO: Replace with actual Supabase/FastAPI call
      console.log('Updating notifications:', notifications);

      toast({
        title: "Preferences updated",
        description: "Your notification preferences have been saved.",
      });

    } catch (error) {
      toast({
        title: "Error",
        description: "Failed to update preferences.",
        variant: "destructive",
      });
    }
  };

  const handleDeleteAccount = async () => {
    setIsDeleting(true);
    try {
      await authService.deleteAccount();

      // Nettoyer et rediriger
      localStorage.removeItem('access_token');
      localStorage.removeItem('refresh_token');

      toast({
        title: "Compte supprimé",
        description: "Votre compte a été supprimé avec succès.",
      });

      // Rediriger vers la page de signup
      navigate('/signup');
    } catch (error) {
      toast({
        title: "Erreur",
        description: "Impossible de supprimer le compte.",
        variant: "destructive",
      });
    } finally {
      setIsDeleting(false);
    }
  };

  return (
    <AppLayout activeHousehold={householdName || activeHousehold}>
      <main className="container mx-auto px-4 py-6 pb-20 md:pb-6">
        <div className="max-w-2xl space-y-6">
          <div>
            <h1 className="text-2xl font-bold text-gray-900 mb-2">Profil & Paramètres</h1>
            <p className="text-gray-600">Gérez votre compte et vos préférences</p>
          </div>

          {/* Pending Invitations */}
          <Card className="shadow-sm border-0 bg-white">
            <CardHeader>
              <CardTitle className="text-lg font-semibold text-gray-900">
                Invitations en attente
              </CardTitle>
            </CardHeader>
            <CardContent>
              {invitesLoading && (
                <div className="text-gray-600">Chargement des invitations…</div>
              )}
              {invitesError && (
                <div className="flex items-center justify-between gap-4">
                  <span className="text-red-600">Échec du chargement des invitations.</span>
                  <Button variant="outline" size="sm" onClick={() => refetchInvites()}>
                    Réessayer
                  </Button>
                </div>
              )}
              {!invitesLoading && !invitesError && invites.length === 0 && (
                <p className="text-gray-600">Aucune invitation en attente.</p>
              )}
              {!invitesLoading && !invitesError && invites.length > 0 && (
                <div className="space-y-3">
                  {invites.map((inv) => (
                    <div key={inv.id} className="flex items-center justify-between p-3 border border-gray-100 rounded-md">
                      <div>
                        <p className="font-medium text-gray-900">{inv.household_name}</p>
                        <p className="text-sm text-gray-600">Rôle : {inv.role}</p>
                      </div>
                      <div className="flex items-center gap-2">
                        <Button
                          size="sm"
                          className="bg-blue-600 hover:bg-blue-700 text-white"
                          disabled={acceptInviteMutation.isPending}
                          onClick={() => acceptInviteMutation.mutate(inv.id)}
                        >
                          Accepter
                        </Button>
                        <Button
                          size="sm"
                          variant="outline"
                          disabled={declineInviteMutation.isPending}
                          onClick={() => declineInviteMutation.mutate(inv.id)}
                        >
                          Refuser
                        </Button>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>

          {/* Personal Information */}
          <Card className="shadow-sm border-0 bg-white">
            <CardHeader>
              <CardTitle className="text-lg font-semibold text-gray-900">
                Informations personnelles
              </CardTitle>
            </CardHeader>
            <CardContent>
              <form onSubmit={handleProfileUpdate} className="space-y-4">
                <div className="space-y-2">
                  <Label htmlFor="name" className="text-sm font-medium text-gray-700">
                    Nom
                  </Label>
                  <div className="relative">
                    <User className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-gray-400" />
                    <Input
                      id="name"
                      type="text"
                      value={profile.name}
                      onChange={(e) => setProfile({ ...profile, name: e.target.value })}
                      className="pl-10"
                    />
                  </div>
                </div>

                <div className="space-y-2">
                  <Label htmlFor="email" className="text-sm font-medium text-gray-700">
                    Adresse email
                  </Label>
                  <div className="relative">
                    <Mail className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-gray-400" />
                    <Input
                      id="email"
                      type="email"
                      value={profile.email}
                      onChange={(e) => setProfile({ ...profile, email: e.target.value })}
                      className="pl-10"
                    />
                  </div>
                </div>

                <Button
                  type="submit"
                  className="bg-blue-600 hover:bg-blue-700 text-white"
                  disabled={isLoading}
                >
                  {isLoading ? (
                    <div className="flex items-center gap-2">
                      <div className="h-4 w-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
                      Mise à jour…
                    </div>
                  ) : (
                    <div className="flex items-center gap-2">
                      <Save className="h-4 w-4" />
                      Mettre à jour le profil
                    </div>
                  )}
                </Button>
              </form>
            </CardContent>
          </Card>

          {/* Change Password */}
          <Card className="shadow-sm border-0 bg-white">
            <CardHeader>
              <CardTitle className="text-lg font-semibold text-gray-900">
                Changer de mot de passe
              </CardTitle>
            </CardHeader>
            <CardContent>
              <form
                className="space-y-4"
                onSubmit={async (e) => {
                  e.preventDefault();
                  // Validations simples
                  if (pwd.next.length < 8) {
                    toast({ title: 'Erreur', description: 'Le nouveau mot de passe doit contenir au moins 8 caractères.', variant: 'destructive' });
                    return;
                  }
                  if (pwd.next !== pwd.confirm) {
                    toast({ title: 'Erreur', description: 'Les mots de passe ne correspondent pas.', variant: 'destructive' });
                    return;
                  }
                  try {
                    await authService.changePassword({ current_password: pwd.current, new_password: pwd.next });
                    toast({ title: 'Mot de passe modifié', description: 'Votre mot de passe a été mis à jour.' });
                    setPwd({ current: '', next: '', confirm: '' });
                  } catch (err: any) {
                    const detail = err?.response?.data?.detail || "Échec du changement de mot de passe.";
                    toast({ title: 'Erreur', description: detail, variant: 'destructive' });
                  }
                }}
              >
                <div className="space-y-2">
                  <Label htmlFor="currentPassword" className="text-sm font-medium text-gray-700">
                    Mot de passe actuel
                  </Label>
                  <div className="relative">
                    <Lock className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-gray-400" />
                    <Input
                      id="currentPassword"
                      type="password"
                      className="pl-10"
                      value={pwd.current}
                      onChange={(e) => setPwd({ ...pwd, current: e.target.value })}
                    />
                  </div>
                </div>

                <div className="space-y-2">
                  <Label htmlFor="newPassword" className="text-sm font-medium text-gray-700">
                    Nouveau mot de passe
                  </Label>
                  <div className="relative">
                    <Lock className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-gray-400" />
                    <Input
                      id="newPassword"
                      type="password"
                      className="pl-10"
                      value={pwd.next}
                      onChange={(e) => setPwd({ ...pwd, next: e.target.value })}
                    />
                  </div>
                </div>

                <div className="space-y-2">
                  <Label htmlFor="confirmPassword" className="text-sm font-medium text-gray-700">
                    Confirmer le nouveau mot de passe
                  </Label>
                  <div className="relative">
                    <Lock className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-gray-400" />
                    <Input
                      id="confirmPassword"
                      type="password"
                      className="pl-10"
                      value={pwd.confirm}
                      onChange={(e) => setPwd({ ...pwd, confirm: e.target.value })}
                    />
                  </div>
                </div>

                <Button type="submit" variant="outline" className="border-gray-200 hover:bg-gray-50">
                  Changer de mot de passe
                </Button>
              </form>
            </CardContent>
          </Card>

          {/* Notification Preferences */}
          <Card className="shadow-sm border-0 bg-white">
            <CardHeader>
              <CardTitle className="text-lg font-semibold text-gray-900 flex items-center gap-2">
                <Bell className="h-5 w-5" />
                Préférences de notification
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="font-medium text-gray-900">Notifications push</p>
                  <p className="text-sm text-gray-600">Recevez des notifications sur votre appareil</p>
                </div>
                <Switch
                  checked={notifications.pushEnabled}
                  onCheckedChange={(checked) =>
                    setNotifications({ ...notifications, pushEnabled: checked })
                  }
                />
              </div>

              <div className="flex items-center justify-between">
                <div>
                  <p className="font-medium text-gray-900">Notifications email</p>
                  <p className="text-sm text-gray-600">Recevez des notifications par e‑mail</p>
                </div>
                <Switch
                  checked={notifications.emailEnabled}
                  onCheckedChange={(checked) =>
                    setNotifications({ ...notifications, emailEnabled: checked })
                  }
                />
              </div>

              <div className="space-y-2">
                <Label className="text-sm font-medium text-gray-700">
                  Délai de rappel (minutes avant)
                </Label>
                <Input
                  type="number"
                  value={notifications.reminderTime}
                  onChange={(e) =>
                    setNotifications({ ...notifications, reminderTime: parseInt(e.target.value) || 0 })
                  }
                  className="w-32"
                />
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label className="text-sm font-medium text-gray-700">
                    Début des heures calmes
                  </Label>
                  <Input
                    type="time"
                    value={notifications.quietHoursStart}
                    onChange={(e) =>
                      setNotifications({ ...notifications, quietHoursStart: e.target.value })
                    }
                  />
                </div>

                <div className="space-y-2">
                  <Label className="text-sm font-medium text-gray-700">
                    Fin des heures calmes
                  </Label>
                  <Input
                    type="time"
                    value={notifications.quietHoursEnd}
                    onChange={(e) =>
                      setNotifications({ ...notifications, quietHoursEnd: e.target.value })
                    }
                  />
                </div>
              </div>

              <Button
                onClick={handleNotificationUpdate}
                variant="outline"
                className="border-gray-200 hover:bg-gray-50"
              >
                Save Preferences
              </Button>
            </CardContent>
          </Card>

          {/* Danger Zone */}
          <Card className="shadow-sm border-0 bg-white border-red-200">
            <CardHeader>
              <CardTitle className="text-lg font-semibold text-red-900">
                Danger Zone
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                <div>
                  <p className="font-medium text-gray-900 mb-2">Delete Account</p>
                  <p className="text-sm text-gray-600 mb-4">
                    Permanently delete your account and all associated data. This action cannot be undone.
                  </p>
                  <AlertDialog>
                    <AlertDialogTrigger asChild>
                      <Button
                        variant="destructive"
                        className="bg-red-600 hover:bg-red-700"
                        disabled={isDeleting}
                      >
                        <Trash2 className="h-4 w-4 mr-2" />
                        Delete Account
                      </Button>
                    </AlertDialogTrigger>
                    <AlertDialogContent>
                      <AlertDialogHeader>
                        <AlertDialogTitle>Are you sure ?</AlertDialogTitle>
                        <AlertDialogDescription>
                          This action will permanently delete your account and all associated data.
                          You will not be able to recover your account after this.
                        </AlertDialogDescription>
                      </AlertDialogHeader>
                      <AlertDialogFooter>
                        <AlertDialogCancel>Annuler</AlertDialogCancel>
                        <AlertDialogAction
                          onClick={handleDeleteAccount}
                          className="bg-red-600 hover:bg-red-700"
                          disabled={isDeleting}
                        >
                          {isDeleting ? 'Suppression...' : 'Supprimer le compte'}
                        </AlertDialogAction>
                      </AlertDialogFooter>
                    </AlertDialogContent>
                  </AlertDialog>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>
      </main>
    </AppLayout>
  );
};

export default Profile;
