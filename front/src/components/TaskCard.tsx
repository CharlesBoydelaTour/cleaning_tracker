
import { Clock, CheckCircle2, AlertTriangle, Calendar, MoreHorizontal } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { cn } from "@/lib/utils";

interface Task {
  id: number;
  title: string;
  description: string;
  room: string;
  assignee: string;
  estimatedDuration: number;
  status: "todo" | "completed" | "overdue";
  dueTime: string;
  completedAt?: string;
  recurrence: string;
}

interface TaskCardProps {
  task: Task;
}

const TaskCard = ({ task }: TaskCardProps) => {
  const getStatusIcon = () => {
    switch (task.status) {
      case "completed":
        return <CheckCircle2 className="h-5 w-5 text-green-600" />;
      case "overdue":
        return <AlertTriangle className="h-5 w-5 text-orange-600" />;
      default:
        return <Clock className="h-5 w-5 text-gray-400" />;
    }
  };

  const getStatusBadge = () => {
    switch (task.status) {
      case "completed":
        return (
          <Badge variant="secondary" className="bg-green-50 text-green-700 border-green-200">
            Completed
          </Badge>
        );
      case "overdue":
        return (
          <Badge variant="destructive" className="bg-orange-100 text-orange-800 border-orange-200">
            Overdue
          </Badge>
        );
      default:
        return (
          <Badge variant="outline" className="border-gray-200 text-gray-600">
            To Do
          </Badge>
        );
    }
  };

  const handleComplete = () => {
    console.log(`Marking task ${task.id} as complete`);
    // Implementation for completing task
  };

  const handleReschedule = () => {
    console.log(`Rescheduling task ${task.id}`);
    // Implementation for rescheduling task
  };

  return (
    <Card className={cn(
      "shadow-sm border-0 bg-white transition-all hover:shadow-md",
      task.status === "completed" && "opacity-75",
      task.status === "overdue" && "border-l-4 border-l-orange-500"
    )}>
      <CardContent className="p-4">
        <div className="flex items-start gap-3">
          {/* Status Icon */}
          <div className="flex-shrink-0 mt-1">
            {getStatusIcon()}
          </div>

          {/* Task Content */}
          <div className="flex-1 min-w-0">
            <div className="flex items-start justify-between gap-2 mb-2">
              <div className="flex-1">
                <h3 className={cn(
                  "font-medium text-gray-900 mb-1",
                  task.status === "completed" && "line-through text-gray-500"
                )}>
                  {task.title}
                </h3>
                <p className="text-sm text-gray-600 mb-2">{task.description}</p>
              </div>
              
              {/* Actions Menu */}
              <DropdownMenu>
                <DropdownMenuTrigger asChild>
                  <Button variant="ghost" size="icon" className="h-8 w-8 flex-shrink-0">
                    <MoreHorizontal className="h-4 w-4" />
                  </Button>
                </DropdownMenuTrigger>
                <DropdownMenuContent align="end">
                  {task.status !== "completed" && (
                    <DropdownMenuItem onClick={handleComplete}>
                      Mark Complete
                    </DropdownMenuItem>
                  )}
                  <DropdownMenuItem onClick={handleReschedule}>
                    Reschedule
                  </DropdownMenuItem>
                  <DropdownMenuItem>Reassign</DropdownMenuItem>
                  <DropdownMenuItem>Edit Task</DropdownMenuItem>
                </DropdownMenuContent>
              </DropdownMenu>
            </div>

            {/* Task Meta Information */}
            <div className="flex flex-wrap items-center gap-3 text-sm text-gray-500">
              <div className="flex items-center gap-1">
                <Calendar className="h-4 w-4" />
                <span>{task.status === "completed" && task.completedAt ? task.completedAt : task.dueTime}</span>
              </div>
              
              <div className="flex items-center gap-1">
                <Clock className="h-4 w-4" />
                <span>{task.estimatedDuration} min</span>
              </div>
              
              <Badge variant="outline" className="border-gray-200 text-gray-600">
                {task.room}
              </Badge>
              
              <span className="text-gray-400">•</span>
              <span>{task.assignee}</span>
            </div>

            {/* Status and Actions */}
            <div className="flex items-center justify-between mt-3">
              {getStatusBadge()}
              
              {task.status === "todo" && (
                <Button 
                  size="sm" 
                  onClick={handleComplete}
                  className="bg-blue-600 hover:bg-blue-700 text-white"
                >
                  Complete
                </Button>
              )}
              
              {task.status === "overdue" && (
                <div className="flex gap-2">
                  <Button 
                    size="sm" 
                    variant="outline"
                    onClick={handleReschedule}
                    className="border-gray-200 hover:bg-gray-50"
                  >
                    Reschedule
                  </Button>
                  <Button 
                    size="sm" 
                    onClick={handleComplete}
                    className="bg-blue-600 hover:bg-blue-700 text-white"
                  >
                    Complete
                  </Button>
                </div>
              )}
            </div>
          </div>
        </div>
      </CardContent>
    </Card>
  );
};

export default TaskCard;
