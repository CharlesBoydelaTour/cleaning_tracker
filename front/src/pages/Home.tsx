import { useState } from "react";
import { Plus, Home as HomeIcon, Settings, Pencil, Trash2, Users } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import AppLayout from "@/components/AppLayout";
import { useCurrentHousehold } from '@/hooks/use-current-household';
import { useAuth } from '@/hooks/use-auth';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { roomsService } from '@/services/rooms.service';
import { membersService } from '@/services/members.service';
import { Room, HouseholdMember } from '@/types/household.types';
import CreateRoomModal from '@/components/CreateRoomModal';
import InviteMemberModal from '@/components/InviteMemberModal';
import MemberCard from '@/components/MemberCard';
import WelcomeScreen from '@/components/WelcomeScreen';
import CreateHouseholdModal from '@/components/CreateHouseholdModal';

const Home = () => {
    const { user, loading: authLoading } = useAuth();
    const {
        householdId,
        householdName,
        loading: householdLoading,
        currentHousehold,
        error: householdError,
        refetch: refetchHousehold
    } = useCurrentHousehold();
    // Si jamais l’utilisateur arrive ici via un lien d’invitation sans passer par /accept-invite,
    // on pourrait détecter les query params et rediriger. L’implémentation dédiée existe déjà.

    const [showCreateRoomModal, setShowCreateRoomModal] = useState(false);
    const [showCreateHouseholdModal, setShowCreateHouseholdModal] = useState(false);
    const [showInviteMemberModal, setShowInviteMemberModal] = useState(false);
    const [activeTab, setActiveTab] = useState('rooms');

    const queryClient = useQueryClient();

    // Query pour récupérer les pièces
    const {
        data: rooms = [],
        isLoading: roomsLoading,
        error: roomsError,
        refetch: refetchRooms
    } = useQuery({
        queryKey: ['rooms', householdId],
        queryFn: () => householdId ? roomsService.getAll(householdId) : Promise.resolve([]),
        enabled: !!householdId,
    });

    // Query pour récupérer les membres
    const {
        data: members = [],
        isLoading: membersLoading,
        error: membersError,
        refetch: refetchMembers
    } = useQuery<HouseholdMember[], Error>({ // Spécifier les types pour data et error
        queryKey: ['members', householdId],
        queryFn: () => householdId ? membersService.getAll(householdId) : Promise.resolve([]),
        enabled: !!householdId,
    });

    // Mutation pour créer une pièce
    const createRoomMutation = useMutation({
        mutationFn: (roomData: { name: string; icon?: string }) =>
            roomsService.create(householdId!, roomData),
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ['rooms', householdId] });
            setShowCreateRoomModal(false);
        },
        onError: (error: any) => {
            console.error('Erreur lors de la création de la pièce:', error);
            alert('Erreur lors de la création de la pièce');
        }
    });

    // Mutation pour supprimer une pièce
    const deleteRoomMutation = useMutation({
        mutationFn: (roomId: string) => roomsService.delete(householdId!, roomId),
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ['rooms', householdId] });
        },
        onError: (error: any) => {
            console.error('Erreur lors de la suppression de la pièce:', error);
            const status = error?.response?.status;
            if (status === 409) {
                alert("Impossible de supprimer la pièce car elle est encore référencée par des tâches. Supprimez ou modifiez ces tâches d'abord.");
            } else if (status === 404) {
                alert("Pièce introuvable ou déjà supprimée.");
            } else if (status === 403) {
                alert("Vous n'avez pas les droits pour supprimer cette pièce.");
            } else {
                alert('Erreur lors de la suppression de la pièce');
            }
        }
    });

    // Mutation pour inviter un membre
    const inviteMemberMutation = useMutation({
        mutationFn: (memberData: { email: string; role: 'admin' | 'member' }) =>
            membersService.invite(householdId!, memberData.email, memberData.role),
        onSuccess: (data) => {
            if (data.status === 'already_pending') {
                alert("Une invitation est déjà en attente pour cet email.");
            } else {
                alert("Invitation envoyée.");
            }
            queryClient.invalidateQueries({ queryKey: ['members', householdId] });
            setShowInviteMemberModal(false);
        },
        onError: (error: any) => {
            console.error('Erreur lors de l\'invitation du membre:', error);
            const detail = error?.response?.data?.detail || error?.message;
            alert(detail || 'Erreur lors de l\'invitation du membre');
        }
    });

    // Mutation pour changer le rôle d'un membre
    const changeRoleMutation = useMutation({
        mutationFn: ({ memberId, role }: { memberId: string; role: 'admin' | 'member' }) =>
            membersService.updateRole(householdId!, memberId, role),
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ['members', householdId] });
        },
        onError: (error: any) => {
            console.error('Erreur lors du changement de rôle:', error);
            alert('Erreur lors du changement de rôle');
        }
    });

    // Mutation pour supprimer un membre
    const removeMemberMutation = useMutation({
        mutationFn: (memberId: string) => membersService.remove(householdId!, memberId),
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ['members', householdId] });
        },
        onError: (error: any) => {
            console.error('Erreur lors de la suppression du membre:', error);
            alert('Erreur lors de la suppression du membre');
        }
    });

    // 1. Gérer le chargement de l'authentification
    // 2. Gérer le chargement du foyer actuel
    // 3. Gérer les erreurs de chargement

    // Déplacement des fonctions de handler ici, avant la section de logging et de return.
    const handleCreateRoom = (roomData: { name: string; icon?: string }) => {
        console.log('handleCreateRoom appelé avec:', roomData);
        console.log('householdId:', householdId);
        if (!householdId) {
            alert("Veuillez d'abord créer un ménage avant d'ajouter une pièce.");
            setShowCreateHouseholdModal(true);
            return;
        }
        createRoomMutation.mutate(roomData);
    };

    const handleDeleteRoom = (roomId: string) => {
        if (confirm('Êtes-vous sûr de vouloir supprimer cette pièce ? Cette action est irréversible.')) {
            deleteRoomMutation.mutate(roomId);
        }
    };

    const handleInviteMember = (memberData: { email: string; role: 'admin' | 'member' }) => {
        inviteMemberMutation.mutate(memberData);
    };

    const handleChangeRole = (memberId: string, role: 'admin' | 'member') => {
        changeRoleMutation.mutate({ memberId, role });
    };

    const handleRemoveMember = (memberId: string) => {
        if (confirm('Êtes-vous sûr de vouloir retirer ce membre du foyer ?')) {
            removeMemberMutation.mutate(memberId);
        }
    };

    // Vérifier si l'utilisateur actuel est admin
    const currentUserMemberInfo = members.find(m => m.user_id === user?.id);
    const isAdmin = !!user && !!currentUserMemberInfo && currentUserMemberInfo.role === 'admin';

    // DEBUG LOGS
    if (activeTab === 'members') {
        console.log('[Home.tsx] Rendering members tab');
        console.log('[Home.tsx] householdId:', householdId);
        console.log('[Home.tsx] membersLoading:', membersLoading);
        console.log('[Home.tsx] membersError:', membersError);
        console.log('[Home.tsx] user:', user ? { id: user.id, email: user.email } : null);
        try {
            console.log('[Home.tsx] currentUserMemberInfo:', JSON.parse(JSON.stringify(currentUserMemberInfo)));
        } catch (e) {
            console.log('[Home.tsx] currentUserMemberInfo (raw):', currentUserMemberInfo);
        }
        console.log('[Home.tsx] isAdmin:', isAdmin);
    }

    // Icônes par défaut pour les pièces
    const defaultIcons = {
        'cuisine': '🍳',
        'salon': '🛋️',
        'chambre': '🛏️',
        'salle de bain': '🚿',
        'salle de bains': '🚿',
        'wc': '🚽',
        'toilettes': '🚽',
        'bureau': '💻',
        'garage': '🚗',
        'jardin': '🌿',
        'cave': '🏠',
        'grenier': '📦',
        'buanderie': '🧺',
        'entrée': '🚪',
        'couloir': '🚪',
    };

    const getRoomIcon = (room: Room): string => {
        if (room.icon) return room.icon;

        const roomNameLower = room.name.toLowerCase();
        for (const [key, icon] of Object.entries(defaultIcons)) {
            if (roomNameLower.includes(key)) {
                return icon;
            }
        }
        return '🏠'; // Icône par défaut
    };

    // Si aucun ménage n'est sélectionné/créé, afficher l'écran de bienvenue
    if (!householdLoading && !householdId) {
        return (
            <AppLayout activeHousehold={"Foyer"}>
                <main className="container mx-auto px-4 py-6 pb-20 md:pb-6">
                    <WelcomeScreen onCreateHousehold={() => setShowCreateHouseholdModal(true)} />
                </main>
                <CreateHouseholdModal
                    open={showCreateHouseholdModal}
                    onOpenChange={setShowCreateHouseholdModal}
                    onSuccess={() => {
                        setShowCreateHouseholdModal(false);
                        refetchHousehold();
                    }}
                />
            </AppLayout>
        );
    }

    return (
        <AppLayout activeHousehold={householdName || "Foyer"}>
            <main className="container mx-auto px-4 py-6 pb-20 md:pb-6">
                {/* Header */}
                <div className="mb-6">
                    <h1 className="text-2xl font-bold text-gray-900 mb-2">Gestion du foyer</h1>
                    <p className="text-gray-600">Gérez les pièces et les membres de votre foyer</p>
                </div>

                {/* Tabs */}
                <Tabs value={activeTab} onValueChange={setActiveTab} className="w-full">
                    <TabsList className="grid w-full grid-cols-2">
                        <TabsTrigger value="rooms" className="flex items-center gap-2">
                            <HomeIcon className="h-4 w-4" />
                            Pièces
                        </TabsTrigger>
                        <TabsTrigger value="members" className="flex items-center gap-2">
                            <Users className="h-4 w-4" />
                            Membres
                        </TabsTrigger>
                    </TabsList>

                    {/* Onglet Pièces */}
                    <TabsContent value="rooms" className="mt-6">
                        <div className="flex items-center justify-between mb-6">
                            <div>
                                <h2 className="text-xl font-semibold text-gray-900">Pièces de votre foyer</h2>
                                <p className="text-gray-600">Gérez les différentes pièces de votre maison</p>
                            </div>
                            <Button
                                onClick={() => setShowCreateRoomModal(true)}
                                disabled={!householdId}
                                className="bg-blue-600 hover:bg-blue-700 disabled:opacity-50"
                            >
                                <Plus className="h-4 w-4 mr-2" />
                                Ajouter une pièce
                            </Button>
                        </div>

                        {/* Loading state */}
                        {roomsLoading && (
                            <div className="flex items-center justify-center h-64">
                                <div className="text-center">
                                    <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mx-auto"></div>
                                    <p className="mt-2 text-gray-600">Chargement des pièces...</p>
                                </div>
                            </div>
                        )}

                        {/* Error state */}
                        {roomsError && (
                            <div className="flex items-center justify-center h-64">
                                <div className="text-center">
                                    <p className="text-red-600">Erreur lors du chargement des pièces</p>
                                    <Button onClick={() => refetchRooms()} className="mt-2">
                                        Réessayer
                                    </Button>
                                </div>
                            </div>
                        )}

                        {/* Rooms Grid */}
                        {!roomsLoading && !roomsError && (
                            <>
                                {rooms.length > 0 ? (
                                    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
                                        {rooms.map((room) => (
                                            <Card key={room.id} className="group hover:shadow-md transition-shadow">
                                                <CardHeader className="pb-3">
                                                    <div className="flex items-center justify-between">
                                                        <div className="flex items-center gap-3">
                                                            <div className="text-2xl">{getRoomIcon(room)}</div>
                                                            <CardTitle className="text-lg">{room.name}</CardTitle>
                                                        </div>
                                                        <div className="flex gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
                                                            <Button
                                                                variant="ghost"
                                                                size="sm"
                                                                className="h-8 w-8 p-0"
                                                                onClick={() => {/* TODO: Implement edit */ }}
                                                            >
                                                                <Pencil className="h-4 w-4" />
                                                            </Button>
                                                            <Button
                                                                variant="ghost"
                                                                size="sm"
                                                                className="h-8 w-8 p-0 text-red-600 hover:text-red-700"
                                                                onClick={() => handleDeleteRoom(room.id)}
                                                            >
                                                                <Trash2 className="h-4 w-4" />
                                                            </Button>
                                                        </div>
                                                    </div>
                                                </CardHeader>
                                                <CardContent>
                                                    <div className="space-y-2">
                                                        <div className="flex justify-between text-sm">
                                                            <span className="text-gray-600">Tâches actives</span>
                                                            <Badge variant="secondary">0</Badge>
                                                        </div>
                                                        <div className="flex justify-between text-sm">
                                                            <span className="text-gray-600">Dernière action</span>
                                                            <span className="text-gray-500">Jamais</span>
                                                        </div>
                                                        <Button
                                                            variant="outline"
                                                            size="sm"
                                                            className="w-full mt-3"
                                                            onClick={() => {/* TODO: Navigate to room detail */ }}
                                                        >
                                                            Voir les détails
                                                        </Button>
                                                    </div>
                                                </CardContent>
                                            </Card>
                                        ))}
                                    </div>
                                ) : (
                                    /* Empty state */
                                    <div className="text-center py-12">
                                        <HomeIcon className="h-16 w-16 mx-auto mb-4 text-gray-300" />
                                        <h3 className="text-xl font-medium mb-2 text-gray-900">Aucune pièce créée</h3>
                                        <p className="text-gray-600 mb-6">
                                            Commencez par ajouter les différentes pièces de votre foyer pour mieux organiser vos tâches ménagères.
                                        </p>
                                        <Button
                                            onClick={() => setShowCreateRoomModal(true)}
                                            className="bg-blue-600 hover:bg-blue-700"
                                        >
                                            <Plus className="h-4 w-4 mr-2" />
                                            Créer votre première pièce
                                        </Button>
                                    </div>
                                )}
                            </>
                        )}
                    </TabsContent>

                    {/* Onglet Membres */}
                    <TabsContent value="members" className="mt-6">
                        <div className="flex items-center justify-between mb-6">
                            <div>
                                <h2 className="text-xl font-semibold text-gray-900">Membres du foyer</h2>
                                <p className="text-gray-600">Gérez les personnes qui font partie de votre foyer</p>
                            </div>
                            {isAdmin && (
                                <Button
                                    onClick={() => setShowInviteMemberModal(true)}
                                    className="bg-green-600 hover:bg-green-700"
                                >
                                    <Plus className="h-4 w-4 mr-2" />
                                    Inviter un membre
                                </Button>
                            )}
                        </div>

                        {/* Loading state */}
                        {membersLoading && (
                            <div className="flex items-center justify-center h-64">
                                <div className="text-center">
                                    <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-green-600 mx-auto"></div>
                                    <p className="mt-2 text-gray-600">Chargement des membres...</p>
                                </div>
                            </div>
                        )}

                        {/* Error state */}
                        {membersError && (
                            <div className="flex items-center justify-center h-64">
                                <div className="text-center">
                                    <p className="text-red-600">Erreur lors du chargement des membres: {membersError.message}</p> {/* Afficher le message d'erreur */}
                                    <Button onClick={() => refetchMembers()} className="mt-2">
                                        Réessayer
                                    </Button>
                                </div>
                            </div>
                        )}

                        {/* Members List */}
                        {!membersLoading && !membersError && currentHousehold && (
                            <>
                                {members.length > 0 ? (
                                    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                                        {members.map((member) => (
                                            <MemberCard
                                                key={member.id}
                                                member={member}
                                                currentUserId={user?.id}
                                                currentUserRole={currentUserMemberInfo?.role} // Utiliser le rôle du membre actuel trouvé
                                                onRoleChange={handleChangeRole}
                                                onRemoveMember={handleRemoveMember}
                                                isUpdating={changeRoleMutation.isPending || removeMemberMutation.isPending}
                                            />
                                        ))}
                                    </div>
                                ) : (
                                    /* Empty state */
                                    <div className="text-center py-12">
                                        <Users className="h-16 w-16 mx-auto mb-4 text-gray-300" />
                                        <h3 className="text-xl font-medium mb-2 text-gray-900">Aucun membre</h3>
                                        <p className="text-gray-600 mb-6">
                                            {isAdmin
                                                ? "Invitez des personnes à rejoindre votre foyer pour partager les tâches ménagères."
                                                : "Seuls les administrateurs peuvent inviter de nouveaux membres."
                                            }
                                        </p>
                                        {isAdmin && (
                                            <Button
                                                onClick={() => setShowInviteMemberModal(true)}
                                                className="bg-green-600 hover:bg-green-700"
                                            >
                                                <Plus className="h-4 w-4 mr-2" />
                                                Inviter le premier membre
                                            </Button>
                                        )}
                                    </div>
                                )}
                            </>
                        )}
                    </TabsContent>
                </Tabs>
            </main>

            <CreateRoomModal
                isOpen={showCreateRoomModal}
                onClose={() => setShowCreateRoomModal(false)}
                onSubmit={handleCreateRoom}
                isLoading={createRoomMutation.isPending}
            />

            <InviteMemberModal
                isOpen={showInviteMemberModal}
                onClose={() => setShowInviteMemberModal(false)}
                onSubmit={handleInviteMember}
                isLoading={inviteMemberMutation.isPending}
            />
            {/* Modal de création de ménage accessible aussi depuis cette page */}
            <CreateHouseholdModal
                open={showCreateHouseholdModal}
                onOpenChange={setShowCreateHouseholdModal}
                onSuccess={() => {
                    setShowCreateHouseholdModal(false);
                    refetchHousehold();
                }}
            />
        </AppLayout>
    );
};

export default Home;
