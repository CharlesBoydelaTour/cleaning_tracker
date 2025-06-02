
import React, { useState } from 'react';
import { Search, Filter, Plus, Clock, Home as HomeIcon, Copy, Edit, Trash2 } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import Header from '@/components/Header';
import Navigation from '@/components/Navigation';
import { Link } from 'react-router-dom';

// Mock data
const mockTasks = [
  {
    id: 1,
    title: "Vacuum living room",
    description: "Weekly deep clean of the living room carpet",
    room: "Living Room",
    estimatedDuration: 30,
    recurrence: "Weekly",
    isGlobal: false
  },
  {
    id: 2,
    title: "Clean bathroom mirrors",
    description: "Wipe down all mirrors in the main bathroom",
    room: "Bathroom",
    estimatedDuration: 15,
    recurrence: "Daily",
    isGlobal: false
  },
  {
    id: 3,
    title: "Take out trash",
    description: "Empty all trash bins and take to curb",
    room: "Kitchen",
    estimatedDuration: 10,
    recurrence: "Twice weekly",
    isGlobal: true
  },
  {
    id: 4,
    title: "Water plants",
    description: "Water all indoor plants",
    room: "Multiple",
    estimatedDuration: 15,
    recurrence: "Every 3 days",
    isGlobal: true
  }
];

const Tasks = () => {
  const [tasks] = useState(mockTasks);
  const [searchTerm, setSearchTerm] = useState('');
  const [activeTab, setActiveTab] = useState('my-tasks');
  const [activeHousehold] = useState("The Smith Family");

  const filteredTasks = tasks.filter(task => {
    const matchesSearch = task.title.toLowerCase().includes(searchTerm.toLowerCase()) ||
                         task.description.toLowerCase().includes(searchTerm.toLowerCase());
    const matchesTab = activeTab === 'my-tasks' ? !task.isGlobal : task.isGlobal;
    return matchesSearch && matchesTab;
  });

  return (
    <div className="min-h-screen bg-gray-50">
      <Header activeHousehold={activeHousehold} />
      
      <main className="container mx-auto px-4 py-6 pb-20 md:pb-6">
        <div className="flex items-center justify-between mb-6">
          <h1 className="text-2xl font-bold text-gray-900">Task Definitions</h1>
          <Link to="/tasks/new">
            <Button className="bg-blue-600 hover:bg-blue-700 text-white">
              <Plus className="h-4 w-4 mr-2" />
              New Task
            </Button>
          </Link>
        </div>

        <div className="flex flex-col sm:flex-row gap-4 mb-6">
          <div className="relative flex-1">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-gray-400" />
            <Input
              placeholder="Search tasks..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="pl-10"
            />
          </div>
          <Button variant="outline" className="border-gray-200 hover:bg-gray-50">
            <Filter className="h-4 w-4 mr-2" />
            Filters
          </Button>
        </div>

        <Tabs value={activeTab} onValueChange={setActiveTab} className="space-y-6">
          <TabsList className="grid w-full grid-cols-2 bg-white">
            <TabsTrigger value="my-tasks">My Tasks</TabsTrigger>
            <TabsTrigger value="global-catalog">Global Catalog</TabsTrigger>
          </TabsList>

          <TabsContent value="my-tasks" className="space-y-4">
            {filteredTasks.length === 0 ? (
              <div className="text-center py-12">
                <div className="text-6xl mb-4">📋</div>
                <h3 className="text-lg font-semibold text-gray-900 mb-2">No tasks found</h3>
                <p className="text-gray-600 mb-6">
                  {searchTerm ? 'Try adjusting your search terms.' : 'Create your first task to get started.'}
                </p>
                {!searchTerm && (
                  <Link to="/tasks/new">
                    <Button className="bg-blue-600 hover:bg-blue-700 text-white">
                      <Plus className="h-4 w-4 mr-2" />
                      Create Your First Task
                    </Button>
                  </Link>
                )}
              </div>
            ) : (
              <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
                {filteredTasks.map((task) => (
                  <Card key={task.id} className="shadow-sm border-0 bg-white hover:shadow-md transition-shadow">
                    <CardHeader className="pb-3">
                      <CardTitle className="text-lg font-semibold text-gray-900">
                        {task.title}
                      </CardTitle>
                      <p className="text-sm text-gray-600">{task.description}</p>
                    </CardHeader>
                    <CardContent className="pt-0 space-y-3">
                      <div className="flex items-center gap-4 text-sm text-gray-600">
                        <div className="flex items-center gap-1">
                          <HomeIcon className="h-4 w-4" />
                          <span>{task.room}</span>
                        </div>
                        <div className="flex items-center gap-1">
                          <Clock className="h-4 w-4" />
                          <span>{task.estimatedDuration}m</span>
                        </div>
                      </div>
                      
                      <Badge variant="secondary" className="bg-gray-100 text-gray-700 border-gray-200">
                        {task.recurrence}
                      </Badge>
                      
                      <div className="flex gap-2 pt-2">
                        <Button variant="ghost" size="sm" className="flex-1 hover:bg-gray-50">
                          <Copy className="h-4 w-4 mr-1" />
                          Duplicate
                        </Button>
                        <Link to={`/tasks/${task.id}/edit`} className="flex-1">
                          <Button variant="ghost" size="sm" className="w-full hover:bg-gray-50">
                            <Edit className="h-4 w-4 mr-1" />
                            Edit
                          </Button>
                        </Link>
                        <Button variant="ghost" size="sm" className="text-red-600 hover:bg-red-50">
                          <Trash2 className="h-4 w-4" />
                        </Button>
                      </div>
                    </CardContent>
                  </Card>
                ))}
              </div>
            )}
          </TabsContent>

          <TabsContent value="global-catalog" className="space-y-4">
            <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
              {filteredTasks.map((task) => (
                <Card key={task.id} className="shadow-sm border-0 bg-white hover:shadow-md transition-shadow">
                  <CardHeader className="pb-3">
                    <CardTitle className="text-lg font-semibold text-gray-900">
                      {task.title}
                    </CardTitle>
                    <p className="text-sm text-gray-600">{task.description}</p>
                  </CardHeader>
                  <CardContent className="pt-0 space-y-3">
                    <div className="flex items-center gap-4 text-sm text-gray-600">
                      <div className="flex items-center gap-1">
                        <HomeIcon className="h-4 w-4" />
                        <span>{task.room}</span>
                      </div>
                      <div className="flex items-center gap-1">
                        <Clock className="h-4 w-4" />
                        <span>{task.estimatedDuration}m</span>
                      </div>
                    </div>
                    
                    <Badge variant="secondary" className="bg-gray-100 text-gray-700 border-gray-200">
                      {task.recurrence}
                    </Badge>
                    
                    <Button className="w-full bg-blue-600 hover:bg-blue-700 text-white">
                      <Plus className="h-4 w-4 mr-2" />
                      Add to My Tasks
                    </Button>
                  </CardContent>
                </Card>
              ))}
            </div>
          </TabsContent>
        </Tabs>
      </main>

      <Navigation />
    </div>
  );
};

export default Tasks;
