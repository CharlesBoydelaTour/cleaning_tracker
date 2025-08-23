
import React, { useState, useEffect } from 'react';
import { Search, Filter, Plus, Clock, Home as HomeIcon, Copy, Edit, Trash2 } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import AppLayout from '@/components/AppLayout';
import { Link } from 'react-router-dom';
import { useTaskOccurrences } from '@/hooks/use-task-occurrences';
import { useCurrentHousehold } from '@/hooks/use-current-household';
import type { TaskOccurrenceWithDefinition } from '@/types/task.types';

const Tasks = () => {
  const { householdId, householdName, loading: householdLoading, error: householdError } = useCurrentHousehold();
  const { tasks, loading, error, fetchTasks } = useTaskOccurrences(householdId);
  interface ExtendedTask extends TaskOccurrenceWithDefinition {
    is_catalog?: boolean;
    estimated_minutes?: number;
    recurrence_rule?: string;
  }
  const [searchTerm, setSearchTerm] = useState('');
  const [activeTab, setActiveTab] = useState('my-tasks');

  useEffect(() => {
    if (householdId) {
      fetchTasks();
    }
  }, [householdId, fetchTasks]);

  const filteredTasks = (tasks as ExtendedTask[]).filter(task => {
    const title = task.definition_title || task.task_title || '';
    const description = task.definition_description || task.task_description || '';
    const isGlobal = task.is_catalog;
    const matchesSearch =
      title.toLowerCase().includes(searchTerm.toLowerCase()) ||
      description.toLowerCase().includes(searchTerm.toLowerCase());
    const matchesTab = activeTab === 'my-tasks' ? !isGlobal : Boolean(isGlobal);
    return matchesSearch && matchesTab;
  });

  if (householdLoading || loading) {
    return (
      <AppLayout activeHousehold={householdName || 'Chargement...'}>
        <div className="container mx-auto px-4 py-6 text-center">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mx-auto" />
          <p className="mt-2 text-gray-600">Chargement des tâches...</p>
        </div>
      </AppLayout>
    );
  }

  if (householdError || error) {
    return (
      <AppLayout activeHousehold={householdName || 'Erreur'}>
        <div className="container mx-auto px-4 py-6 text-center">
          <p className="text-red-600">Erreur lors du chargement des tâches : {householdError || error}</p>
          <Button onClick={() => fetchTasks()} className="mt-2">
            Réessayer
          </Button>
        </div>
      </AppLayout>
    );
  }

  return (
    <AppLayout activeHousehold={householdName || ''}>
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
                {filteredTasks.map((task) => {
                  const title = task.definition_title || task.task_title;
                  const description = task.definition_description || task.task_description;
                  const room = task.room_name || 'N/A';
                  const duration = task.estimated_minutes;
                  const recurrence = task.recurrence_rule || 'Récurrent';
                  return (
                    <Card key={task.id} className="shadow-sm border-0 bg-white hover:shadow-md transition-shadow">
                      <CardHeader className="pb-3">
                        <CardTitle className="text-lg font-semibold text-gray-900">
                          {title}
                        </CardTitle>
                        <p className="text-sm text-gray-600">{description}</p>
                      </CardHeader>
                      <CardContent className="pt-0 space-y-3">
                        <div className="flex items-center gap-4 text-sm text-gray-600">
                          <div className="flex items-center gap-1">
                            <HomeIcon className="h-4 w-4" />
                            <span>{room}</span>
                          </div>
                          <div className="flex items-center gap-1">
                            <Clock className="h-4 w-4" />
                            <span>{duration ? `${duration}m` : '--'}</span>
                          </div>
                        </div>

                        <Badge variant="secondary" className="bg-gray-100 text-gray-700 border-gray-200">
                          {recurrence}
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
                  );
                })}
              </div>
            )}
          </TabsContent>

          <TabsContent value="global-catalog" className="space-y-4">
            <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
              {filteredTasks.map((task) => {
                const title = task.definition_title || task.task_title;
                const description = task.definition_description || task.task_description;
                const room = task.room_name || 'N/A';
                const duration = task.estimated_minutes;
                const recurrence = task.recurrence_rule || 'Récurrent';
                return (
                  <Card key={task.id} className="shadow-sm border-0 bg-white hover:shadow-md transition-shadow">
                    <CardHeader className="pb-3">
                      <CardTitle className="text-lg font-semibold text-gray-900">
                        {title}
                      </CardTitle>
                      <p className="text-sm text-gray-600">{description}</p>
                    </CardHeader>
                    <CardContent className="pt-0 space-y-3">
                      <div className="flex items-center gap-4 text-sm text-gray-600">
                        <div className="flex items-center gap-1">
                          <HomeIcon className="h-4 w-4" />
                          <span>{room}</span>
                        </div>
                        <div className="flex items-center gap-1">
                          <Clock className="h-4 w-4" />
                          <span>{duration ? `${duration}m` : '--'}</span>
                        </div>
                      </div>

                      <Badge variant="secondary" className="bg-gray-100 text-gray-700 border-gray-200">
                        {recurrence}
                      </Badge>

                      <Button className="w-full bg-blue-600 hover:bg-blue-700 text-white">
                        <Plus className="h-4 w-4 mr-2" />
                        Add to My Tasks
                      </Button>
                    </CardContent>
                  </Card>
                );
              })}
            </div>
          </TabsContent>
        </Tabs>
      </main>
    </AppLayout>
  );
};

export default Tasks;
