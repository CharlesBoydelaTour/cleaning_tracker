
import React, { useState } from 'react';
import { BarChart3, TrendingUp, Clock, Users, Download } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Progress } from '@/components/ui/progress';
import Header from '@/components/Header';
import Navigation from '@/components/Navigation';

const Statistics = () => {
  const [period, setPeriod] = useState('week');
  const [activeHousehold] = useState("The Smith Family");

  // Mock statistics data
  const stats = {
    completionRate: 85,
    overdueTasks: 3,
    totalTimeSpent: 240, // minutes
    tasksCompleted: 17,
    memberStats: [
      { name: "Sarah", completed: 8, overdue: 1, timeSpent: 120 },
      { name: "Mike", completed: 6, overdue: 1, timeSpent: 90 },
      { name: "Emma", completed: 3, overdue: 1, timeSpent: 30 }
    ],
    roomStats: [
      { name: "Kitchen", tasks: 8, completion: 90 },
      { name: "Living Room", tasks: 5, completion: 80 },
      { name: "Bathroom", tasks: 4, completion: 75 },
      { name: "Bedroom", tasks: 3, completion: 100 }
    ],
    recentTasks: [
      { title: "Vacuum living room", assignee: "Sarah", duration: 25, estimated: 30, date: "2024-05-20" },
      { title: "Clean bathroom", assignee: "Mike", duration: 20, estimated: 15, date: "2024-05-20" },
      { title: "Kitchen cleanup", assignee: "Emma", duration: 30, estimated: 25, date: "2024-05-19" }
    ]
  };

  const handleExport = (format: 'csv' | 'pdf') => {
    // TODO: Implement export functionality
    console.log(`Exporting data as ${format}`);
  };

  return (
    <div className="min-h-screen bg-gray-50">
      <Header activeHousehold={activeHousehold} />
      
      <main className="container mx-auto px-4 py-6 pb-20 md:pb-6">
        <div className="flex items-center justify-between mb-6">
          <div>
            <h1 className="text-2xl font-bold text-gray-900 flex items-center gap-2">
              <BarChart3 className="h-6 w-6" />
              Statistics
            </h1>
            <p className="text-gray-600">Track your household's performance and progress</p>
          </div>
          
          <div className="flex items-center gap-2">
            <Select value={period} onValueChange={setPeriod}>
              <SelectTrigger className="w-32">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="week">This Week</SelectItem>
                <SelectItem value="month">This Month</SelectItem>
                <SelectItem value="year">This Year</SelectItem>
              </SelectContent>
            </Select>
            
            <Button variant="outline" className="border-gray-200 hover:bg-gray-50">
              <Download className="h-4 w-4 mr-2" />
              Export
            </Button>
          </div>
        </div>

        {/* Key Performance Indicators */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
          <Card className="shadow-sm border-0 bg-white">
            <CardContent className="p-4">
              <div className="flex items-center gap-3">
                <div className="h-10 w-10 bg-green-100 rounded-lg flex items-center justify-center">
                  <TrendingUp className="h-5 w-5 text-green-600" />
                </div>
                <div>
                  <p className="text-sm text-gray-600">Completion Rate</p>
                  <p className="text-2xl font-bold text-gray-900">{stats.completionRate}%</p>
                </div>
              </div>
            </CardContent>
          </Card>

          <Card className="shadow-sm border-0 bg-white">
            <CardContent className="p-4">
              <div className="flex items-center gap-3">
                <div className="h-10 w-10 bg-blue-100 rounded-lg flex items-center justify-center">
                  <BarChart3 className="h-5 w-5 text-blue-600" />
                </div>
                <div>
                  <p className="text-sm text-gray-600">Tasks Completed</p>
                  <p className="text-2xl font-bold text-gray-900">{stats.tasksCompleted}</p>
                </div>
              </div>
            </CardContent>
          </Card>

          <Card className="shadow-sm border-0 bg-white">
            <CardContent className="p-4">
              <div className="flex items-center gap-3">
                <div className="h-10 w-10 bg-orange-100 rounded-lg flex items-center justify-center">
                  <Clock className="h-5 w-5 text-orange-600" />
                </div>
                <div>
                  <p className="text-sm text-gray-600">Overdue Tasks</p>
                  <p className="text-2xl font-bold text-gray-900">{stats.overdueTasks}</p>
                </div>
              </div>
            </CardContent>
          </Card>

          <Card className="shadow-sm border-0 bg-white">
            <CardContent className="p-4">
              <div className="flex items-center gap-3">
                <div className="h-10 w-10 bg-purple-100 rounded-lg flex items-center justify-center">
                  <Clock className="h-5 w-5 text-purple-600" />
                </div>
                <div>
                  <p className="text-sm text-gray-600">Time Spent</p>
                  <p className="text-2xl font-bold text-gray-900">{Math.floor(stats.totalTimeSpent / 60)}h {stats.totalTimeSpent % 60}m</p>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>

        <div className="grid gap-6 lg:grid-cols-2">
          {/* Member Performance */}
          <Card className="shadow-sm border-0 bg-white">
            <CardHeader>
              <CardTitle className="text-lg font-semibold text-gray-900 flex items-center gap-2">
                <Users className="h-5 w-5" />
                Member Performance
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              {stats.memberStats.map((member, index) => (
                <div key={index} className="space-y-2">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-3">
                      <div className="h-8 w-8 bg-blue-100 rounded-full flex items-center justify-center">
                        <span className="text-sm font-medium text-blue-600">
                          {member.name.slice(0, 2)}
                        </span>
                      </div>
                      <span className="font-medium text-gray-900">{member.name}</span>
                    </div>
                    <div className="text-right">
                      <p className="text-sm font-medium text-gray-900">
                        {member.completed} completed
                      </p>
                      <p className="text-xs text-gray-600">
                        {member.timeSpent}m total
                      </p>
                    </div>
                  </div>
                  <Progress 
                    value={(member.completed / (member.completed + member.overdue)) * 100} 
                    className="h-2" 
                  />
                </div>
              ))}
            </CardContent>
          </Card>

          {/* Room Activity */}
          <Card className="shadow-sm border-0 bg-white">
            <CardHeader>
              <CardTitle className="text-lg font-semibold text-gray-900">
                Activity by Room
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              {stats.roomStats.map((room, index) => (
                <div key={index} className="space-y-2">
                  <div className="flex items-center justify-between">
                    <span className="font-medium text-gray-900">{room.name}</span>
                    <div className="text-right">
                      <p className="text-sm font-medium text-gray-900">
                        {room.completion}% complete
                      </p>
                      <p className="text-xs text-gray-600">
                        {room.tasks} tasks
                      </p>
                    </div>
                  </div>
                  <Progress value={room.completion} className="h-2" />
                </div>
              ))}
            </CardContent>
          </Card>

          {/* Recent Task Performance */}
          <Card className="shadow-sm border-0 bg-white lg:col-span-2">
            <CardHeader>
              <CardTitle className="text-lg font-semibold text-gray-900">
                Recent Task Performance
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="overflow-x-auto">
                <table className="w-full">
                  <thead>
                    <tr className="border-b border-gray-200">
                      <th className="text-left py-2 text-sm font-medium text-gray-700">Task</th>
                      <th className="text-left py-2 text-sm font-medium text-gray-700">Assignee</th>
                      <th className="text-left py-2 text-sm font-medium text-gray-700">Estimated</th>
                      <th className="text-left py-2 text-sm font-medium text-gray-700">Actual</th>
                      <th className="text-left py-2 text-sm font-medium text-gray-700">Variance</th>
                      <th className="text-left py-2 text-sm font-medium text-gray-700">Date</th>
                    </tr>
                  </thead>
                  <tbody>
                    {stats.recentTasks.map((task, index) => {
                      const variance = task.duration - task.estimated;
                      const variancePercent = Math.round((variance / task.estimated) * 100);
                      
                      return (
                        <tr key={index} className="border-b border-gray-100">
                          <td className="py-3 text-sm text-gray-900">{task.title}</td>
                          <td className="py-3 text-sm text-gray-600">{task.assignee}</td>
                          <td className="py-3 text-sm text-gray-600">{task.estimated}m</td>
                          <td className="py-3 text-sm text-gray-600">{task.duration}m</td>
                          <td className="py-3 text-sm">
                            <span className={variance > 0 ? 'text-red-600' : variance < 0 ? 'text-green-600' : 'text-gray-600'}>
                              {variance > 0 ? '+' : ''}{variancePercent}%
                            </span>
                          </td>
                          <td className="py-3 text-sm text-gray-600">{task.date}</td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Export Options */}
        <Card className="shadow-sm border-0 bg-white mt-6">
          <CardHeader>
            <CardTitle className="text-lg font-semibold text-gray-900">
              Export Data
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="flex flex-wrap gap-3">
              <Button 
                onClick={() => handleExport('csv')}
                variant="outline" 
                className="border-gray-200 hover:bg-gray-50"
              >
                <Download className="h-4 w-4 mr-2" />
                Export as CSV
              </Button>
              <Button 
                onClick={() => handleExport('pdf')}
                variant="outline" 
                className="border-gray-200 hover:bg-gray-50"
              >
                <Download className="h-4 w-4 mr-2" />
                Export as PDF
              </Button>
            </div>
          </CardContent>
        </Card>
      </main>

      <Navigation />
    </div>
  );
};

export default Statistics;
