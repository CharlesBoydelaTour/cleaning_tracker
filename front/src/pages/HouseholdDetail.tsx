
import React, { useState } from 'react';
import { ArrowLeft, Users, Home as HomeIcon, Settings, UserPlus, Plus, Crown, Trash2 } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import Header from '@/components/Header';
import Navigation from '@/components/Navigation';
import { Link, useParams } from 'react-router-dom';

// Mock data
const mockHousehold = {
  id: 1,
  name: "The Smith Family",
  members: [
    { id: 1, name: "Sarah Smith", email: "sarah@example.com", role: "Admin", avatar: "SS" },
    { id: 2, name: "Mike Smith", email: "mike@example.com", role: "Member", avatar: "MS" },
    { id: 3, name: "Emma Smith", email: "emma@example.com", role: "Member", avatar: "ES" },
  ],
  rooms: [
    { id: 1, name: "Living Room", icon: "🛋️", taskCount: 5 },
    { id: 2, name: "Kitchen", icon: "🍳", taskCount: 8 },
    { id: 3, name: "Bathroom", icon: "🚿", taskCount: 4 },
    { id: 4, name: "Bedroom", icon: "🛏️", taskCount: 3 },
  ]
};

const HouseholdDetail = () => {
  const { id } = useParams();
  const [household] = useState(mockHousehold);
  const [activeTab, setActiveTab] = useState("members");

  return (
    <div className="min-h-screen bg-gray-50">
      <Header activeHousehold={household.name} />
      
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
                Members ({household.members.length})
              </h2>
              <Button className="bg-blue-600 hover:bg-blue-700 text-white">
                <UserPlus className="h-4 w-4 mr-2" />
                Invite Member
              </Button>
            </div>

            <div className="space-y-3">
              {household.members.map((member) => (
                <Card key={member.id} className="shadow-sm border-0 bg-white">
                  <CardContent className="p-4">
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-3">
                        <div className="h-10 w-10 bg-blue-100 rounded-full flex items-center justify-center">
                          <span className="text-sm font-medium text-blue-600">{member.avatar}</span>
                        </div>
                        <div>
                          <div className="flex items-center gap-2">
                            <p className="font-medium text-gray-900">{member.name}</p>
                            {member.role === 'Admin' && (
                              <Crown className="h-4 w-4 text-yellow-500" />
                            )}
                          </div>
                          <p className="text-sm text-gray-600">{member.email}</p>
                        </div>
                      </div>
                      <div className="flex items-center gap-2">
                        <Badge 
                          variant={member.role === 'Admin' ? 'default' : 'secondary'}
                          className={member.role === 'Admin' 
                            ? 'bg-blue-100 text-blue-800 border-blue-200' 
                            : 'bg-gray-100 text-gray-700 border-gray-200'
                          }
                        >
                          {member.role}
                        </Badge>
                        {member.role !== 'Admin' && (
                          <Button variant="ghost" size="sm" className="text-red-600 hover:bg-red-50">
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
                Rooms ({household.rooms.length})
              </h2>
              <Button className="bg-blue-600 hover:bg-blue-700 text-white">
                <Plus className="h-4 w-4 mr-2" />
                Add Room
              </Button>
            </div>

            <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4">
              {household.rooms.map((room) => (
                <Card key={room.id} className="shadow-sm border-0 bg-white hover:shadow-md transition-shadow cursor-pointer">
                  <CardContent className="p-4 text-center">
                    <div className="text-3xl mb-2">{room.icon}</div>
                    <h3 className="font-medium text-gray-900 mb-1">{room.name}</h3>
                    <p className="text-sm text-gray-600">{room.taskCount} tasks</p>
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

      <Navigation />
    </div>
  );
};

export default HouseholdDetail;
