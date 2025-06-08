import { useState } from "react";
import { Plus, Home as HomeIcon, Settings, Pencil, Trash2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import AppLayout from "@/components/AppLayout";
import { useCurrentHousehold } from '@/hooks/use-current-household';
import { useAuth } from '@/hooks/use-auth';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { roomsService } from '@/services/rooms.service';
import { Room } from '@/types/household.types';
import CreateRoomModal from '@/components/CreateRoomModal';
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

    const [showCreateRoomModal, setShowCreateRoomModal] = useState(false);
    const [showCreateHouseholdModal, setShowCreateHouseholdModal] = useState(false);

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
            alert('Erreur lors de la suppression de la pièce');
        }
    });

    // 1. Gérer le chargement de l'authentification
    if (authLoading) {
        return (
            <AppLayout activeHousehold="Chargement...">
                <div className="container mx-auto px-4 py-6 text-center">Chargement des informations utilisateur...</div>
            </AppLayout>
        );
    }

    // 2. Gérer le cas où l'utilisateur n'est pas authentifié
    if (!user) {
        return (
            <AppLayout activeHousehold="Connexion requise">
                <div className="container mx-auto px-4 py-6 text-center">Veuillez vous connecter pour accéder à cette page.</div>
            </AppLayout>
        );
    }

    // 3. Gérer le chargement du ménage
    if (householdLoading) {
        return (
            <AppLayout activeHousehold="Chargement...">
                <div className="container mx-auto px-4 py-6 text-center">Chargement des informations du foyer...</div>
            </AppLayout>
        );
    }

    // 4. Gérer l'erreur de chargement du ménage
    if (householdError) {
        return (
            <AppLayout activeHousehold="Erreur">
                <div className="container mx-auto px-4 py-6 text-center">
                    <p className="text-red-600">Erreur lors du chargement du foyer : {householdError}</p>
                    <Button onClick={() => refetchHousehold && refetchHousehold()} className="mt-2">
                        Réessayer
                    </Button>
                </div>
            </AppLayout>
        );
    }

    // 5. Si aucun foyer n'est trouvé
    if (!currentHousehold) {
        return (
            <AppLayout activeHousehold="Bienvenue">
                <WelcomeScreen onCreateHousehold={() => setShowCreateHouseholdModal(true)} />
                <CreateHouseholdModal
                    open={showCreateHouseholdModal}
                    onOpenChange={setShowCreateHouseholdModal}
                    onSuccess={() => {
                        setShowCreateHouseholdModal(false);
                        if (refetchHousehold) {
                            refetchHousehold();
                        } else {
                            window.location.reload();
                        }
                    }}
                />
            </AppLayout>
        );
    }

    const handleCreateRoom = (roomData: { name: string; icon?: string }) => {
        createRoomMutation.mutate(roomData);
    };

    const handleDeleteRoom = (roomId: string) => {
        if (confirm('Êtes-vous sûr de vouloir supprimer cette pièce ? Cette action est irréversible.')) {
            deleteRoomMutation.mutate(roomId);
        }
    };

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

    return (
        <AppLayout activeHousehold={householdName || "Foyer"}>
            <main className="container mx-auto px-4 py-6 pb-20 md:pb-6">
                {/* Header */}
                <div className="flex items-center justify-between mb-6">
                    <div>
                        <h1 className="text-2xl font-bold text-gray-900">Pièces de votre foyer</h1>
                        <p className="text-gray-600">Gérez les différentes pièces de votre maison</p>
                    </div>
                    <Button
                        onClick={() => setShowCreateRoomModal(true)}
                        className="bg-blue-600 hover:bg-blue-700"
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
            </main>

            <CreateRoomModal
                isOpen={showCreateRoomModal}
                onClose={() => setShowCreateRoomModal(false)}
                onSubmit={handleCreateRoom}
                isLoading={createRoomMutation.isPending}
            />
        </AppLayout>
    );
};

export default Home;
