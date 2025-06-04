
import { useEffect, useState } from "react";
import { Calendar, BarChart3, Settings, Plus, CheckCircle2, Clock, AlertTriangle } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Progress } from "@/components/ui/progress";
import Header from "@/components/Header";
import TaskCard from "@/components/TaskCard";
import Navigation from "@/components/Navigation";
import { EmailVerificationBanner } from '@/components/EmailVerificationBanner';
import { useHouseholds } from '@/contexts/HouseholdContext';
import { tasksService } from '@/services/tasks.service';


const Index = () => {
  const { activeHousehold } = useHouseholds();
  const [tasks, setTasks] = useState<any[]>([]);

  useEffect(() => {
    if (!activeHousehold) return;
    const today = new Date().toISOString().slice(0, 10);
    tasksService
      .listOccurrences(activeHousehold.id, { start_date: today, end_date: today })
      .then((data) => {
        const mapped = data.map((occ) => ({
          id: occ.id,
          title: occ.task_title,
          description: occ.task_description,
          room: occ.room_name,
          assignee: occ.assigned_user_email || '',
          estimatedDuration: occ.estimated_minutes || 0,
          status:
            occ.status === 'done'
              ? 'completed'
              : occ.status === 'overdue'
              ? 'overdue'
              : 'todo',
          dueTime: occ.due_at ? new Date(occ.due_at).toLocaleTimeString() : '',
        }));
        setTasks(mapped);
      })
      .catch((err) => console.error(err));
  }, [activeHousehold]);

  const completedTasks = tasks.filter((t) => t.status === 'completed');
  const overdueTasks = tasks.filter((t) => t.status === 'overdue');
  const todoTasks = tasks.filter((t) => t.status === 'todo');

  const todayTasks = tasks;

  const completionRate = Math.round((completedTasks.length / todayTasks.length) * 100);

  return (
    <div className="min-h-screen bg-gray-50">
      <Header activeHousehold={activeHousehold?.name} />

      <div className="container mx-auto px-4">
        <EmailVerificationBanner />
      </div>

      <main className="container mx-auto px-4 py-6 pb-20 md:pb-6">
        {/* Today Overview Card */}
        <Card className="mb-6 shadow-sm border-0 bg-white">
          <CardHeader className="pb-4">
            <div className="flex items-center justify-between">
              <CardTitle className="text-xl font-semibold text-gray-900">Today's Overview</CardTitle>
              <Badge variant="secondary" className="bg-blue-50 text-blue-700 border-blue-200">
                {new Date().toLocaleDateString('en-US', { weekday: 'long', month: 'short', day: 'numeric' })}
              </Badge>
            </div>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              <div className="text-center">
                <div className="text-2xl font-bold text-gray-900">{todayTasks.length}</div>
                <div className="text-sm text-gray-600">Total Tasks</div>
              </div>
              <div className="text-center">
                <div className="text-2xl font-bold text-green-600">{completedTasks.length}</div>
                <div className="text-sm text-gray-600">Completed</div>
              </div>
              <div className="text-center">
                <div className="text-2xl font-bold text-orange-600">{overdueTasks.length}</div>
                <div className="text-sm text-gray-600">Overdue</div>
              </div>
              <div className="text-center">
                <div className="text-2xl font-bold text-blue-600">{todoTasks.length}</div>
                <div className="text-sm text-gray-600">Remaining</div>
              </div>
            </div>

            <div className="space-y-2">
              <div className="flex justify-between text-sm">
                <span className="text-gray-600">Daily Progress</span>
                <span className="font-medium text-gray-900">{completionRate}% Complete</span>
              </div>
              <Progress value={completionRate} className="h-2" />
            </div>
          </CardContent>
        </Card>

        {/* Quick Actions */}
        <div className="flex gap-3 mb-6 overflow-x-auto pb-2">
          <Button className="flex-shrink-0 bg-blue-600 hover:bg-blue-700 text-white">
            <Plus className="h-4 w-4 mr-2" />
            New Task
          </Button>
          <Button variant="outline" className="flex-shrink-0 border-gray-200 hover:bg-gray-50">
            <Calendar className="h-4 w-4 mr-2" />
            Calendar
          </Button>
          <Button variant="outline" className="flex-shrink-0 border-gray-200 hover:bg-gray-50">
            <BarChart3 className="h-4 w-4 mr-2" />
            Statistics
          </Button>
          <Button variant="outline" className="flex-shrink-0 border-gray-200 hover:bg-gray-50">
            <Settings className="h-4 w-4 mr-2" />
            Settings
          </Button>
        </div>

        {/* Overdue Tasks */}
        {overdueTasks.length > 0 && (
          <div className="mb-6">
            <div className="flex items-center gap-2 mb-4">
              <AlertTriangle className="h-5 w-5 text-orange-600" />
              <h2 className="text-lg font-semibold text-gray-900">Overdue Tasks</h2>
              <Badge variant="destructive" className="bg-orange-100 text-orange-800 border-orange-200">
                {overdueTasks.length}
              </Badge>
            </div>
            <div className="space-y-3">
              {overdueTasks.map(task => (
                <TaskCard key={task.id} task={task} />
              ))}
            </div>
          </div>
        )}

        {/* Today's Tasks */}
        <div className="mb-6">
          <div className="flex items-center gap-2 mb-4">
            <Clock className="h-5 w-5 text-blue-600" />
            <h2 className="text-lg font-semibold text-gray-900">Today's Tasks</h2>
          </div>
          <div className="space-y-3">
            {todoTasks.map(task => (
              <TaskCard key={task.id} task={task} />
            ))}
          </div>
        </div>

        {/* Completed Tasks */}
        {completedTasks.length > 0 && (
          <div>
            <div className="flex items-center gap-2 mb-4">
              <CheckCircle2 className="h-5 w-5 text-green-600" />
              <h2 className="text-lg font-semibold text-gray-900">Completed Today</h2>
              <Badge variant="secondary" className="bg-green-50 text-green-700 border-green-200">
                {completedTasks.length}
              </Badge>
            </div>
            <div className="space-y-3">
              {completedTasks.map(task => (
                <TaskCard key={task.id} task={task} />
              ))}
            </div>
          </div>
        )}
      </main>

      <Navigation />
    </div>
  );
};

export default Index;
