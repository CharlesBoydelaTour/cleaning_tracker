
import React, { useState } from 'react';
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
  const { logout } = useAuth();
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const { householdName, refetch: refetchHousehold } = useCurrentHousehold();
  const [isDeleting, setIsDeleting] = useState(false);
  const [activeHousehold] = useState<string | undefined>(undefined);
  const [profile, setProfile] = useState({
    name: 'Sarah Smith',
    email: 'sarah@example.com'
  });

  const [notifications, setNotifications] = useState({
    pushEnabled: true,
    emailEnabled: true,
    reminderTime: 60,
    quietHoursStart: '22:00',
    quietHoursEnd: '07:00'
  });

  const [isLoading, setIsLoading] = useState(false);

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
      // TODO: Replace with actual Supabase/FastAPI call
      console.log('Updating profile:', profile);

      await new Promise(resolve => setTimeout(resolve, 1000));

      toast({
        title: "Profile updated",
        description: "Your profile has been updated successfully.",
      });

    } catch (error) {
      toast({
        title: "Error",
        description: "Failed to update profile.",
        variant: "destructive",
      });
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
            <h1 className="text-2xl font-bold text-gray-900 mb-2">Profile & Settings</h1>
            <p className="text-gray-600">Manage your account and preferences</p>
          </div>

          {/* Pending Invitations */}
          <Card className="shadow-sm border-0 bg-white">
            <CardHeader>
              <CardTitle className="text-lg font-semibold text-gray-900">
                Pending Household Invitations
              </CardTitle>
            </CardHeader>
            <CardContent>
              {invitesLoading && (
                <div className="text-gray-600">Loading invites...</div>
              )}
              {invitesError && (
                <div className="flex items-center justify-between gap-4">
                  <span className="text-red-600">Failed to load invites.</span>
                  <Button variant="outline" size="sm" onClick={() => refetchInvites()}>
                    Retry
                  </Button>
                </div>
              )}
              {!invitesLoading && !invitesError && invites.length === 0 && (
                <p className="text-gray-600">No pending invitations.</p>
              )}
              {!invitesLoading && !invitesError && invites.length > 0 && (
                <div className="space-y-3">
                  {invites.map((inv) => (
                    <div key={inv.id} className="flex items-center justify-between p-3 border border-gray-100 rounded-md">
                      <div>
                        <p className="font-medium text-gray-900">{inv.household_name}</p>
                        <p className="text-sm text-gray-600">Role: {inv.role}</p>
                      </div>
                      <div className="flex items-center gap-2">
                        <Button
                          size="sm"
                          className="bg-blue-600 hover:bg-blue-700 text-white"
                          disabled={acceptInviteMutation.isPending}
                          onClick={() => acceptInviteMutation.mutate(inv.id)}
                        >
                          Accept
                        </Button>
                        <Button
                          size="sm"
                          variant="outline"
                          disabled={declineInviteMutation.isPending}
                          onClick={() => declineInviteMutation.mutate(inv.id)}
                        >
                          Decline
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
                Personal Information
              </CardTitle>
            </CardHeader>
            <CardContent>
              <form onSubmit={handleProfileUpdate} className="space-y-4">
                <div className="space-y-2">
                  <Label htmlFor="name" className="text-sm font-medium text-gray-700">
                    Full Name
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
                    Email Address
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
                      Updating...
                    </div>
                  ) : (
                    <div className="flex items-center gap-2">
                      <Save className="h-4 w-4" />
                      Update Profile
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
                Change Password
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                <div className="space-y-2">
                  <Label htmlFor="currentPassword" className="text-sm font-medium text-gray-700">
                    Current Password
                  </Label>
                  <div className="relative">
                    <Lock className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-gray-400" />
                    <Input
                      id="currentPassword"
                      type="password"
                      className="pl-10"
                    />
                  </div>
                </div>

                <div className="space-y-2">
                  <Label htmlFor="newPassword" className="text-sm font-medium text-gray-700">
                    New Password
                  </Label>
                  <div className="relative">
                    <Lock className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-gray-400" />
                    <Input
                      id="newPassword"
                      type="password"
                      className="pl-10"
                    />
                  </div>
                </div>

                <div className="space-y-2">
                  <Label htmlFor="confirmPassword" className="text-sm font-medium text-gray-700">
                    Confirm New Password
                  </Label>
                  <div className="relative">
                    <Lock className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-gray-400" />
                    <Input
                      id="confirmPassword"
                      type="password"
                      className="pl-10"
                    />
                  </div>
                </div>

                <Button variant="outline" className="border-gray-200 hover:bg-gray-50">
                  Change Password
                </Button>
              </div>
            </CardContent>
          </Card>

          {/* Notification Preferences */}
          <Card className="shadow-sm border-0 bg-white">
            <CardHeader>
              <CardTitle className="text-lg font-semibold text-gray-900 flex items-center gap-2">
                <Bell className="h-5 w-5" />
                Notification Preferences
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="font-medium text-gray-900">Push Notifications</p>
                  <p className="text-sm text-gray-600">Receive notifications on your device</p>
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
                  <p className="font-medium text-gray-900">Email Notifications</p>
                  <p className="text-sm text-gray-600">Receive notifications via email</p>
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
                  Reminder Time (minutes before)
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
                    Quiet Hours Start
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
                    Quiet Hours End
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
