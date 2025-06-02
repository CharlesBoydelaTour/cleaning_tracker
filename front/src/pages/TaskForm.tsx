
import React, { useState } from 'react';
import { ArrowLeft, Save, Clock, Home as HomeIcon, Calendar } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Textarea } from '@/components/ui/textarea';
import { Label } from '@/components/ui/label';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { useToast } from '@/hooks/use-toast';
import Header from '@/components/Header';
import Navigation from '@/components/Navigation';
import { Link, useParams, useNavigate } from 'react-router-dom';

const TaskForm = () => {
  const { id } = useParams();
  const navigate = useNavigate();
  const { toast } = useToast();
  const isEdit = Boolean(id);
  
  const [formData, setFormData] = useState({
    title: isEdit ? 'Vacuum living room' : '',
    description: isEdit ? 'Weekly deep clean of the living room carpet' : '',
    room: isEdit ? 'living-room' : '',
    estimatedDuration: isEdit ? 30 : '',
    recurrence: isEdit ? 'weekly' : 'once'
  });
  
  const [isLoading, setIsLoading] = useState(false);
  const [activeHousehold] = useState("The Smith Family");

  const rooms = [
    { value: 'living-room', label: 'Living Room' },
    { value: 'kitchen', label: 'Kitchen' },
    { value: 'bathroom', label: 'Bathroom' },
    { value: 'bedroom', label: 'Bedroom' },
    { value: 'multiple', label: 'Multiple Rooms' }
  ];

  const recurrenceOptions = [
    { value: 'once', label: 'One-time' },
    { value: 'daily', label: 'Daily' },
    { value: 'weekly', label: 'Weekly' },
    { value: 'biweekly', label: 'Twice weekly' },
    { value: 'monthly', label: 'Monthly' },
    { value: 'custom', label: 'Custom...' }
  ];

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsLoading(true);

    try {
      // TODO: Replace with actual Supabase/FastAPI call
      console.log(isEdit ? 'Updating task:' : 'Creating task:', formData);
      
      // Simulate API call
      await new Promise(resolve => setTimeout(resolve, 1000));
      
      toast({
        title: isEdit ? "Task updated" : "Task created",
        description: isEdit ? "Your task has been updated successfully." : "Your new task has been created.",
      });
      
      navigate('/tasks');
      
    } catch (error) {
      toast({
        title: "Error",
        description: isEdit ? "Failed to update task." : "Failed to create task.",
        variant: "destructive",
      });
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gray-50">
      <Header activeHousehold={activeHousehold} />
      
      <main className="container mx-auto px-4 py-6 pb-20 md:pb-6">
        <div className="flex items-center gap-4 mb-6">
          <Link to="/tasks">
            <Button variant="ghost" size="sm" className="p-2">
              <ArrowLeft className="h-4 w-4" />
            </Button>
          </Link>
          <div>
            <h1 className="text-2xl font-bold text-gray-900">
              {isEdit ? 'Edit Task' : 'Create New Task'}
            </h1>
            <p className="text-gray-600">
              {isEdit ? 'Update task details and schedule' : 'Define a new task for your household'}
            </p>
          </div>
        </div>

        <div className="max-w-2xl">
          <Card className="shadow-sm border-0 bg-white">
            <CardHeader>
              <CardTitle className="text-lg font-semibold text-gray-900">
                Task Details
              </CardTitle>
            </CardHeader>
            <CardContent>
              <form onSubmit={handleSubmit} className="space-y-6">
                <div className="space-y-2">
                  <Label htmlFor="title" className="text-sm font-medium text-gray-700">
                    Task Title *
                  </Label>
                  <Input
                    id="title"
                    type="text"
                    placeholder="e.g., Vacuum living room"
                    value={formData.title}
                    onChange={(e) => setFormData({ ...formData, title: e.target.value })}
                    required
                  />
                </div>

                <div className="space-y-2">
                  <Label htmlFor="description" className="text-sm font-medium text-gray-700">
                    Description
                  </Label>
                  <Textarea
                    id="description"
                    placeholder="Describe what needs to be done..."
                    value={formData.description}
                    onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                    rows={3}
                  />
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <Label className="text-sm font-medium text-gray-700">
                      Room *
                    </Label>
                    <Select 
                      value={formData.room} 
                      onValueChange={(value) => setFormData({ ...formData, room: value })}
                    >
                      <SelectTrigger>
                        <div className="flex items-center gap-2">
                          <HomeIcon className="h-4 w-4 text-gray-400" />
                          <SelectValue placeholder="Select a room" />
                        </div>
                      </SelectTrigger>
                      <SelectContent>
                        {rooms.map((room) => (
                          <SelectItem key={room.value} value={room.value}>
                            {room.label}
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>

                  <div className="space-y-2">
                    <Label htmlFor="duration" className="text-sm font-medium text-gray-700">
                      Estimated Duration (minutes)
                    </Label>
                    <div className="relative">
                      <Clock className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-gray-400" />
                      <Input
                        id="duration"
                        type="number"
                        placeholder="30"
                        value={formData.estimatedDuration}
                        onChange={(e) => setFormData({ ...formData, estimatedDuration: parseInt(e.target.value) || '' })}
                        className="pl-10"
                        min="1"
                      />
                    </div>
                  </div>
                </div>

                <div className="space-y-2">
                  <Label className="text-sm font-medium text-gray-700">
                    Recurrence *
                  </Label>
                  <Select 
                    value={formData.recurrence} 
                    onValueChange={(value) => setFormData({ ...formData, recurrence: value })}
                  >
                    <SelectTrigger>
                      <div className="flex items-center gap-2">
                        <Calendar className="h-4 w-4 text-gray-400" />
                        <SelectValue placeholder="Select recurrence" />
                      </div>
                    </SelectTrigger>
                    <SelectContent>
                      {recurrenceOptions.map((option) => (
                        <SelectItem key={option.value} value={option.value}>
                          {option.label}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>

                {formData.recurrence && formData.recurrence !== 'once' && (
                  <Card className="bg-blue-50 border-blue-200">
                    <CardContent className="p-4">
                      <h4 className="font-medium text-blue-900 mb-2">30-Day Preview</h4>
                      <p className="text-sm text-blue-700">
                        This task will occur approximately {
                          formData.recurrence === 'daily' ? '30 times' :
                          formData.recurrence === 'weekly' ? '4-5 times' :
                          formData.recurrence === 'biweekly' ? '8-9 times' :
                          formData.recurrence === 'monthly' ? '1 time' : 'X times'
                        } in the next 30 days.
                      </p>
                    </CardContent>
                  </Card>
                )}

                <div className="flex gap-3 pt-4">
                  <Button
                    type="submit"
                    className="flex-1 bg-blue-600 hover:bg-blue-700 text-white"
                    disabled={isLoading}
                  >
                    {isLoading ? (
                      <div className="flex items-center gap-2">
                        <div className="h-4 w-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
                        {isEdit ? 'Updating...' : 'Creating...'}
                      </div>
                    ) : (
                      <div className="flex items-center gap-2">
                        <Save className="h-4 w-4" />
                        {isEdit ? 'Update Task' : 'Create Task'}
                      </div>
                    )}
                  </Button>
                  <Link to="/tasks">
                    <Button variant="outline" className="border-gray-200 hover:bg-gray-50">
                      Cancel
                    </Button>
                  </Link>
                </div>
              </form>
            </CardContent>
          </Card>
        </div>
      </main>

      <Navigation />
    </div>
  );
};

export default TaskForm;
