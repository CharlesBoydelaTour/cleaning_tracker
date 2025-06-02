
import React, { useState } from 'react';
import { Home, Users, Plus, Settings } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import Header from '@/components/Header';
import Navigation from '@/components/Navigation';
import { Link } from 'react-router-dom';

// Mock data
const mockHouseholds = [
  {
    id: 1,
    name: "The Smith Family",
    role: "Admin",
    memberCount: 4,
    isActive: true
  },
  {
    id: 2,
    name: "Downtown Apartment",
    role: "Member",
    memberCount: 2,
    isActive: false
  }
];

const Households = () => {
  const [households] = useState(mockHouseholds);
  const [activeHousehold] = useState("The Smith Family");

  const handleSelectHousehold = (householdId: number) => {
    // TODO: Implement household selection logic
    console.log('Selected household:', householdId);
  };

  return (
    <div className="min-h-screen bg-gray-50">
      <Header activeHousehold={activeHousehold} />
      
      <main className="container mx-auto px-4 py-6 pb-20 md:pb-6">
        <div className="flex items-center justify-between mb-6">
          <h1 className="text-2xl font-bold text-gray-900">My Households</h1>
          <Button className="bg-blue-600 hover:bg-blue-700 text-white">
            <Plus className="h-4 w-4 mr-2" />
            Create Household
          </Button>
        </div>

        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
          {households.map((household) => (
            <Card key={household.id} className="shadow-sm border-0 bg-white hover:shadow-md transition-shadow">
              <CardHeader className="pb-3">
                <div className="flex items-start justify-between">
                  <div className="flex items-center gap-3">
                    <div className="h-10 w-10 bg-blue-100 rounded-lg flex items-center justify-center">
                      <Home className="h-5 w-5 text-blue-600" />
                    </div>
                    <div>
                      <CardTitle className="text-lg font-semibold text-gray-900">
                        {household.name}
                      </CardTitle>
                      <div className="flex items-center gap-2 mt-1">
                        <Badge 
                          variant={household.role === 'Admin' ? 'default' : 'secondary'}
                          className={household.role === 'Admin' 
                            ? 'bg-blue-100 text-blue-800 border-blue-200' 
                            : 'bg-gray-100 text-gray-700 border-gray-200'
                          }
                        >
                          {household.role}
                        </Badge>
                        {household.isActive && (
                          <Badge className="bg-green-100 text-green-800 border-green-200">
                            Active
                          </Badge>
                        )}
                      </div>
                    </div>
                  </div>
                </div>
              </CardHeader>
              <CardContent className="pt-0">
                <div className="flex items-center gap-2 text-sm text-gray-600 mb-4">
                  <Users className="h-4 w-4" />
                  <span>{household.memberCount} members</span>
                </div>
                
                <div className="flex gap-2">
                  {!household.isActive && (
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => handleSelectHousehold(household.id)}
                      className="flex-1 border-blue-200 text-blue-600 hover:bg-blue-50"
                    >
                      Select
                    </Button>
                  )}
                  <Link to={`/households/${household.id}`} className="flex-1">
                    <Button variant="outline" size="sm" className="w-full border-gray-200 hover:bg-gray-50">
                      <Settings className="h-4 w-4 mr-1" />
                      Manage
                    </Button>
                  </Link>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>

        {households.length === 0 && (
          <div className="text-center py-12">
            <Home className="h-16 w-16 text-gray-300 mx-auto mb-4" />
            <h3 className="text-lg font-semibold text-gray-900 mb-2">No households yet</h3>
            <p className="text-gray-600 mb-6">Create your first household to start organizing chores.</p>
            <Button className="bg-blue-600 hover:bg-blue-700 text-white">
              <Plus className="h-4 w-4 mr-2" />
              Create Your First Household
            </Button>
          </div>
        )}
      </main>

      <Navigation />
    </div>
  );
};

export default Households;
