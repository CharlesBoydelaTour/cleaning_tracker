
import React, { useState } from 'react';
import { ArrowLeft, Clock, MapPin, User, Camera, Calendar, MessageSquare } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Textarea } from '@/components/ui/textarea';
import { useToast } from '@/hooks/use-toast';
import AppLayout from '@/components/AppLayout';
import { Link, useParams } from 'react-router-dom';

const OccurrenceDetail = () => {
  const { id } = useParams();
  const { toast } = useToast();
  const [activeHousehold] = useState("The Smith Family");
  const [comment, setComment] = useState('');
  const [duration, setDuration] = useState('');

  // Mock occurrence data
  const occurrence = {
    id: 1,
    title: "Vacuum living room",
    description: "Weekly deep clean of the living room carpet including under furniture",
    room: "Living Room",
    assignee: "Sarah Smith",
    scheduledTime: "10:00 AM",
    estimatedDuration: 30,
    status: "todo" as "todo" | "completed" | "overdue",
    recurrence: "Weekly",
    history: [
      { date: "2024-05-20", completedBy: "Mike", duration: 25, comment: "Moved all furniture for thorough cleaning" },
      { date: "2024-05-13", completedBy: "Sarah", duration: 30, comment: "Standard weekly vacuum" },
    ]
  };

  const handleComplete = async () => {
    try {
      // TODO: Replace with actual Supabase/FastAPI call
      console.log('Completing task:', { id, duration, comment });

      toast({
        title: "Task completed",
        description: "Great job! The task has been marked as complete.",
      });

    } catch (error) {
      toast({
        title: "Error",
        description: "Failed to complete task.",
        variant: "destructive",
      });
    }
  };

  const handleReschedule = () => {
    // TODO: Implement reschedule logic
    toast({
      title: "Reschedule",
      description: "Reschedule functionality will be implemented here.",
    });
  };

  const handleSkip = () => {
    // TODO: Implement skip logic
    toast({
      title: "Task skipped",
      description: "This occurrence has been skipped.",
    });
  };

  const handleReassign = () => {
    // TODO: Implement reassign logic
    toast({
      title: "Reassign",
      description: "Reassign functionality will be implemented here.",
    });
  };

  return (
    <AppLayout activeHousehold={activeHousehold}>
      <main className="container mx-auto px-4 py-6 pb-20 md:pb-6">
        <div className="flex items-center gap-4 mb-6">
          <Link to="/calendar">
            <Button variant="ghost" size="sm" className="p-2">
              <ArrowLeft className="h-4 w-4" />
            </Button>
          </Link>
          <div className="flex-1">
            <div className="flex items-center gap-3 mb-1">
              <h1 className="text-2xl font-bold text-gray-900">{occurrence.title}</h1>
              <Badge
                variant="secondary"
                className={
                  occurrence.status === 'completed' ? 'bg-green-100 text-green-800 border-green-200' :
                    occurrence.status === 'overdue' ? 'bg-red-100 text-red-800 border-red-200' :
                      'bg-blue-100 text-blue-800 border-blue-200'
                }
              >
                {occurrence.status}
              </Badge>
            </div>
            <p className="text-gray-600">Scheduled for today at {occurrence.scheduledTime}</p>
          </div>
        </div>

        <div className="grid gap-6 lg:grid-cols-3">
          {/* Main Content */}
          <div className="lg:col-span-2 space-y-6">
            {/* Task Information */}
            <Card className="shadow-sm border-0 bg-white">
              <CardHeader>
                <CardTitle className="text-lg font-semibold text-gray-900">
                  Task Information
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <p className="text-gray-700">{occurrence.description}</p>

                <div className="grid grid-cols-2 gap-4">
                  <div className="flex items-center gap-3">
                    <MapPin className="h-5 w-5 text-gray-400" />
                    <div>
                      <p className="text-sm text-gray-600">Room</p>
                      <p className="font-medium text-gray-900">{occurrence.room}</p>
                    </div>
                  </div>

                  <div className="flex items-center gap-3">
                    <User className="h-5 w-5 text-gray-400" />
                    <div>
                      <p className="text-sm text-gray-600">Assigned to</p>
                      <p className="font-medium text-gray-900">{occurrence.assignee}</p>
                    </div>
                  </div>

                  <div className="flex items-center gap-3">
                    <Clock className="h-5 w-5 text-gray-400" />
                    <div>
                      <p className="text-sm text-gray-600">Estimated Duration</p>
                      <p className="font-medium text-gray-900">{occurrence.estimatedDuration} minutes</p>
                    </div>
                  </div>

                  <div className="flex items-center gap-3">
                    <Calendar className="h-5 w-5 text-gray-400" />
                    <div>
                      <p className="text-sm text-gray-600">Recurrence</p>
                      <p className="font-medium text-gray-900">{occurrence.recurrence}</p>
                    </div>
                  </div>
                </div>
              </CardContent>
            </Card>

            {/* Complete Task */}
            {occurrence.status === 'todo' && (
              <Card className="shadow-sm border-0 bg-white">
                <CardHeader>
                  <CardTitle className="text-lg font-semibold text-gray-900">
                    Complete Task
                  </CardTitle>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-2">
                        Actual Duration (minutes)
                      </label>
                      <input
                        type="number"
                        value={duration}
                        onChange={(e) => setDuration(e.target.value)}
                        className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                        placeholder="30"
                      />
                    </div>

                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-2">
                        Add Photo
                      </label>
                      <Button variant="outline" className="w-full border-gray-300 hover:bg-gray-50">
                        <Camera className="h-4 w-4 mr-2" />
                        Take Photo
                      </Button>
                    </div>
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Comments (optional)
                    </label>
                    <Textarea
                      value={comment}
                      onChange={(e) => setComment(e.target.value)}
                      placeholder="Any notes about this task..."
                      rows={3}
                    />
                  </div>

                  <Button
                    onClick={handleComplete}
                    className="w-full bg-green-600 hover:bg-green-700 text-white"
                  >
                    Mark as Complete
                  </Button>
                </CardContent>
              </Card>
            )}

            {/* Task History */}
            <Card className="shadow-sm border-0 bg-white">
              <CardHeader>
                <CardTitle className="text-lg font-semibold text-gray-900">
                  Recent History
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  {occurrence.history.map((entry, index) => (
                    <div key={index} className="border-l-2 border-gray-200 pl-4 pb-4">
                      <div className="flex items-center justify-between mb-2">
                        <p className="font-medium text-gray-900">{entry.completedBy}</p>
                        <p className="text-sm text-gray-600">{entry.date}</p>
                      </div>
                      <div className="flex items-center gap-4 text-sm text-gray-600 mb-2">
                        <span>Duration: {entry.duration} minutes</span>
                      </div>
                      {entry.comment && (
                        <div className="flex items-start gap-2">
                          <MessageSquare className="h-4 w-4 text-gray-400 mt-0.5" />
                          <p className="text-sm text-gray-700">{entry.comment}</p>
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          </div>

          {/* Actions Sidebar */}
          <div className="space-y-4">
            <Card className="shadow-sm border-0 bg-white">
              <CardHeader>
                <CardTitle className="text-lg font-semibold text-gray-900">
                  Actions
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-3">
                <Button
                  onClick={handleReschedule}
                  variant="outline"
                  className="w-full border-gray-200 hover:bg-gray-50"
                >
                  <Calendar className="h-4 w-4 mr-2" />
                  Reschedule
                </Button>

                <Button
                  onClick={handleReassign}
                  variant="outline"
                  className="w-full border-gray-200 hover:bg-gray-50"
                >
                  <User className="h-4 w-4 mr-2" />
                  Reassign
                </Button>

                <Button
                  onClick={handleSkip}
                  variant="outline"
                  className="w-full border-orange-200 text-orange-600 hover:bg-orange-50"
                >
                  Skip This Time
                </Button>
              </CardContent>
            </Card>
          </div>
        </div>
      </main>
    </AppLayout>
  );
};

export default OccurrenceDetail;
