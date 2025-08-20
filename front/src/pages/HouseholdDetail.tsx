
import React, { useState } from 'react';
import {
  ArrowLeft,
  Users,
  Home as HomeIcon,
  Settings,
  UserPlus,
  Plus,
  Crown,
  Trash2,
} from 'lucide-react';
import { useQuery } from '@tanstack/react-query';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import AppLayout from '@/components/AppLayout';
import { Link, useParams } from 'react-router-dom';
import { householdsService } from '@/services/households.service';
import type { Household, HouseholdMember, Room } from '@/types';

const HouseholdDetail = () => {
  const { id } = useParams();
  const householdId = id as string;
  const [activeTab, setActiveTab] = useState('members');

  const householdQuery = useQuery<Household>({
    queryKey: ['household', householdId],
    queryFn: () => householdsService.getById(householdId),
    enabled: !!householdId,
  });

  const membersQuery = useQuery<HouseholdMember[]>({
    queryKey: ['household', householdId, 'members'],
    queryFn: () => householdsService.getMembers(householdId),
    enabled: !!householdId,
  });

  const roomsQuery = useQuery<Room[]>({
    queryKey: ['household', householdId, 'rooms'],
    queryFn: () => householdsService.getRooms(householdId),
    enabled: !!householdId,
  });

  const isLoading =
    householdQuery.isLoading || membersQuery.isLoading || roomsQuery.isLoading;
  const isError =
    householdQuery.isError || membersQuery.isError || roomsQuery.isError;

  const handleRetry = () => {
    householdQuery.refetch();
    membersQuery.refetch();
    roomsQuery.refetch();
  };

  if (isLoading) {
    return (
      <AppLayout>
        <main className="container mx-auto px-4 py-6 pb-20 md:pb-6">
          <p>Loading household...</p>
        </main>
      </AppLayout>
    );
  }

  if (isError || !householdQuery.data) {
    return (
      <AppLayout>
        <main className="container mx-auto px-4 py-6 pb-20 md:pb-6 text-center">
          <p className="mb-2">Failed to load household.</p>
          <Button variant="outline" onClick={handleRetry}>
            Retry
          </Button>
        </main>
      </AppLayout>
    );
  }

  const household = householdQuery.data;
  const members = membersQuery.data ?? [];
  const rooms = roomsQuery.data ?? [];

  return (
    <AppLayout activeHousehold={household.name}>
      <main className="container mx-auto px-4 py-6 pb-20 md:pb-6">
        <div className="flex items-center gap-4 mb-6">
          <Link to="/households">
            <Button variant="ghost" size="sm" className="p-2">
              <ArrowLeft className="h-4 w-4" />
            </Button>
          </Link>
          <div>
            <h1 className="text-2xl font-bold text-gray-900">{household.name}</h1>
            <p className="text-gray-600">Manage members, rooms, and settings</p>
          </div>
        </div>

        <Tabs value={activeTab} onValueChange={setActiveTab} className="space-y-6">
          <TabsList className="grid w-full grid-cols-3 bg-white">
            <TabsTrigger value="members" className="flex items-center gap-2">
              <Users className="h-4 w-4" />
              Members
            </TabsTrigger>
            <TabsTrigger value="rooms" className="flex items-center gap-2">
              <HomeIcon className="h-4 w-4" />
              Rooms
            </TabsTrigger>
            <TabsTrigger value="settings" className="flex items-center gap-2">
              <Settings className="h-4 w-4" />
              Settings
            </TabsTrigger>
          </TabsList>

          <TabsContent value="members" className="space-y-4">
            <div className="flex items-center justify-between">
              <h2 className="text-lg font-semibold text-gray-900">
                Members ({members.length})
              </h2>
              <Button className="bg-blue-600 hover:bg-blue-700 text-white">
                <UserPlus className="h-4 w-4 mr-2" />
                Invite Member
              </Button>
            </div>

            <div className="space-y-3">
              {members.map((member) => (
                <Card key={member.id} className="shadow-sm border-0 bg-white">
                  <CardContent className="p-4">
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-3">
                        <div className="h-10 w-10 bg-blue-100 rounded-full flex items-center justify-center">
                          <span className="text-sm font-medium text-blue-600">
                            {member.user_full_name?.slice(0, 2).toUpperCase()}
                          </span>
                        </div>
                        <div>
                          <div className="flex items-center gap-2">
                            <p className="font-medium text-gray-900">
                              {member.user_full_name}
                            </p>
                            {member.role === 'admin' && (
                              <Crown className="h-4 w-4 text-yellow-500" />
                            )}
                          </div>
                          <p className="text-sm text-gray-600">{member.user_email}</p>
                        </div>
                      </div>
                      <div className="flex items-center gap-2">
                        <Badge
                          variant={member.role === 'admin' ? 'default' : 'secondary'}
                          className={
                            member.role === 'admin'
                              ? 'bg-blue-100 text-blue-800 border-blue-200'
                              : 'bg-gray-100 text-gray-700 border-gray-200'
                          }
                        >
                          {member.role}
                        </Badge>
                        {member.role !== 'admin' && (
                          <Button
                            variant="ghost"
                            size="sm"
                            className="text-red-600 hover:bg-red-50"
                          >
                            <Trash2 className="h-4 w-4" />
                          </Button>
                        )}
                      </div>
                    </div>
                  </CardContent>
                </Card>
              ))}
            </div>
          </TabsContent>

          <TabsContent value="rooms" className="space-y-4">
            <div className="flex items-center justify-between">
              <h2 className="text-lg font-semibold text-gray-900">
                Rooms ({rooms.length})
              </h2>
              <Button className="bg-blue-600 hover:bg-blue-700 text-white">
                <Plus className="h-4 w-4 mr-2" />
                Add Room
              </Button>
            </div>

            <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4">
              {rooms.map((room) => (
                <Card
                  key={room.id}
                  className="shadow-sm border-0 bg-white hover:shadow-md transition-shadow cursor-pointer"
                >
                  <CardContent className="p-4 text-center">
                    <div className="text-3xl mb-2">{room.icon ?? '🏠'}</div>
                    <h3 className="font-medium text-gray-900 mb-1">{room.name}</h3>
                  </CardContent>
                </Card>
              ))}
            </div>
          </TabsContent>

          <TabsContent value="settings" className="space-y-4">
            <Card className="shadow-sm border-0 bg-white">
              <CardHeader>
                <CardTitle className="text-lg font-semibold text-gray-900">
                  Household Settings
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Household Name
                  </label>
                  <div className="flex gap-2">
                    <input
                      type="text"
                      value={household.name}
                      className="flex-1 px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                      readOnly
                    />
                    <Button variant="outline">Edit</Button>
                  </div>
                </div>

                <div className="pt-4 border-t">
                  <h3 className="text-sm font-medium text-gray-900 mb-4">Danger Zone</h3>
                  <Button variant="destructive" className="bg-red-600 hover:bg-red-700">
                    <Trash2 className="h-4 w-4 mr-2" />
                    Delete Household
                  </Button>
                  <p className="text-xs text-gray-500 mt-2">
                    This action cannot be undone. This will permanently delete the household and all associated data.
                  </p>
                </div>
              </CardContent>
            </Card>
          </TabsContent>
        </Tabs>
      </main>
    </AppLayout>
  );
};

export default HouseholdDetail;
