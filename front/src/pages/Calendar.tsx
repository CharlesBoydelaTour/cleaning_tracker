
import React, { useState } from 'react';
import { ChevronLeft, ChevronRight, Filter, Calendar as CalendarIcon } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Card, CardContent } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import AppLayout from '@/components/AppLayout';

const Calendar = () => {
  const [currentDate, setCurrentDate] = useState(new Date());
  const [view, setView] = useState<'day' | 'week' | 'month'>('month');
  const [activeHousehold] = useState("The Smith Family");

  // Mock calendar events
  const events = [
    {
      id: 1,
      title: "Vacuum living room",
      time: "10:00 AM",
      status: "todo" as const,
      assignee: "Sarah",
      room: "Living Room"
    },
    {
      id: 2,
      title: "Clean bathroom mirrors",
      time: "9:00 AM",
      status: "completed" as const,
      assignee: "Mike",
      room: "Bathroom"
    },
    {
      id: 3,
      title: "Take out trash",
      time: "8:00 AM",
      status: "overdue" as const,
      assignee: "Sarah",
      room: "Kitchen"
    }
  ];

  const getDaysInMonth = (date: Date) => {
    const year = date.getFullYear();
    const month = date.getMonth();
    const firstDay = new Date(year, month, 1);
    const lastDay = new Date(year, month + 1, 0);
    const daysInMonth = lastDay.getDate();
    const startingDayOfWeek = firstDay.getDay();

    const days = [];

    // Add empty cells for days before the first day of the month
    for (let i = 0; i < startingDayOfWeek; i++) {
      days.push(null);
    }

    // Add days of the month
    for (let day = 1; day <= daysInMonth; day++) {
      days.push(day);
    }

    return days;
  };

  const navigateMonth = (direction: 'prev' | 'next') => {
    setCurrentDate(prev => {
      const newDate = new Date(prev);
      if (direction === 'prev') {
        newDate.setMonth(prev.getMonth() - 1);
      } else {
        newDate.setMonth(prev.getMonth() + 1);
      }
      return newDate;
    });
  };

  const monthNames = [
    'January', 'February', 'March', 'April', 'May', 'June',
    'July', 'August', 'September', 'October', 'November', 'December'
  ];

  const dayNames = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'];

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'completed': return 'bg-green-500';
      case 'overdue': return 'bg-red-500';
      default: return 'bg-blue-500';
    }
  };

  return (
    <AppLayout activeHousehold={activeHousehold}>
      <main className="container mx-auto px-4 py-6 pb-20 md:pb-6">
        <div className="flex items-center justify-between mb-6">
          <h1 className="text-2xl font-bold text-gray-900">Calendar</h1>
          <div className="flex items-center gap-2">
            <Button variant="outline" className="border-gray-200 hover:bg-gray-50">
              <Filter className="h-4 w-4 mr-2" />
              Filters
            </Button>
            <div className="flex bg-white border border-gray-200 rounded-md">
              {(['day', 'week', 'month'] as const).map((viewOption) => (
                <Button
                  key={viewOption}
                  variant={view === viewOption ? 'default' : 'ghost'}
                  size="sm"
                  onClick={() => setView(viewOption)}
                  className={view === viewOption ? 'bg-blue-600 text-white' : 'hover:bg-gray-50'}
                >
                  {viewOption.charAt(0).toUpperCase() + viewOption.slice(1)}
                </Button>
              ))}
            </div>
          </div>
        </div>

        <Card className="shadow-sm border-0 bg-white">
          <CardContent className="p-6">
            <div className="flex items-center justify-between mb-6">
              <h2 className="text-xl font-semibold text-gray-900">
                {monthNames[currentDate.getMonth()]} {currentDate.getFullYear()}
              </h2>
              <div className="flex items-center gap-2">
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => navigateMonth('prev')}
                  className="border-gray-200 hover:bg-gray-50"
                >
                  <ChevronLeft className="h-4 w-4" />
                </Button>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => setCurrentDate(new Date())}
                  className="border-gray-200 hover:bg-gray-50"
                >
                  Today
                </Button>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => navigateMonth('next')}
                  className="border-gray-200 hover:bg-gray-50"
                >
                  <ChevronRight className="h-4 w-4" />
                </Button>
              </div>
            </div>

            {view === 'month' && (
              <div className="grid grid-cols-7 gap-1">
                {dayNames.map((day) => (
                  <div key={day} className="p-2 text-center text-sm font-medium text-gray-600 border-b">
                    {day}
                  </div>
                ))}

                {getDaysInMonth(currentDate).map((day, index) => (
                  <div key={index} className="min-h-[100px] border border-gray-100 p-2">
                    {day && (
                      <>
                        <div className="text-sm font-medium text-gray-900 mb-1">{day}</div>
                        {day === new Date().getDate() &&
                          currentDate.getMonth() === new Date().getMonth() &&
                          currentDate.getFullYear() === new Date().getFullYear() && (
                            <div className="space-y-1">
                              {events.map((event) => (
                                <div
                                  key={event.id}
                                  className="text-xs p-1 rounded bg-gray-50 border-l-2 border-blue-500 cursor-pointer hover:bg-gray-100"
                                >
                                  <div className="flex items-center gap-1">
                                    <div className={`w-2 h-2 rounded-full ${getStatusColor(event.status)}`} />
                                    <span className="font-medium truncate">{event.title}</span>
                                  </div>
                                  <div className="text-gray-600">{event.time}</div>
                                </div>
                              ))}
                            </div>
                          )}
                      </>
                    )}
                  </div>
                ))}
              </div>
            )}

            {view === 'day' && (
              <div className="space-y-4">
                <h3 className="text-lg font-semibold text-gray-900">
                  {new Date().toLocaleDateString('en-US', {
                    weekday: 'long',
                    month: 'long',
                    day: 'numeric'
                  })}
                </h3>
                <div className="space-y-2">
                  {events.map((event) => (
                    <Card key={event.id} className="border-l-4 border-blue-500 hover:shadow-md transition-shadow cursor-pointer">
                      <CardContent className="p-4">
                        <div className="flex items-center justify-between">
                          <div>
                            <h4 className="font-medium text-gray-900">{event.title}</h4>
                            <p className="text-sm text-gray-600">{event.room} • {event.time}</p>
                          </div>
                          <div className="flex items-center gap-2">
                            <Badge
                              variant="secondary"
                              className={
                                event.status === 'completed' ? 'bg-green-100 text-green-800 border-green-200' :
                                  event.status === 'overdue' ? 'bg-red-100 text-red-800 border-red-200' :
                                    'bg-blue-100 text-blue-800 border-blue-200'
                              }
                            >
                              {event.status}
                            </Badge>
                            <div className="h-8 w-8 bg-blue-100 rounded-full flex items-center justify-center">
                              <span className="text-xs font-medium text-blue-600">
                                {event.assignee.slice(0, 2)}
                              </span>
                            </div>
                          </div>
                        </div>
                      </CardContent>
                    </Card>
                  ))}
                </div>
              </div>
            )}
          </CardContent>
        </Card>
      </main>
    </AppLayout>
  );
};

export default Calendar;
