
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
  priority?: 'low' | 'medium' | 'high';
  // Id de la définition (utilisé pour modifier la tâche)
  definitionId?: string;
}

interface TaskCardProps {
  task: Task;
  onComplete?: (taskId: number, data?: { duration_minutes?: number; comment?: string; photo_url?: string }) => Promise<void>;
  onEdit?: (definitionId: string) => void;
}

const TaskCard = ({ task, onComplete, onEdit }: TaskCardProps) => {
  const getStatusIcon = () => {
    switch (task.status) {
      case "completed":
        return <CheckCircle2 className="h-5 w-5 text-green-600" />;
      case "overdue":
        return <AlertTriangle className="h-5 w-5 text-red-600" />;
      default:
        return <Clock className="h-5 w-5 text-gray-400" />;
    }
  };

  const getStatusBadge = () => {
    switch (task.status) {
      case "completed":
        return (
          <Badge variant="secondary" className="bg-green-50 text-green-700 border-green-200">
            Terminé
          </Badge>
        );
      case "overdue":
        return (
          <Badge variant="destructive" className="bg-red-100 text-red-800 border-red-200">
            En retard
          </Badge>
        );
      default:
        return (
          <Badge variant="outline" className="border-gray-200 text-gray-600">
            À faire
          </Badge>
        );
    }
  };

  const getPriorityBadge = () => {
    const p = task.priority || 'medium';
    if (p === 'high') {
      return <Badge className="bg-red-100 text-red-800 border-red-200">Priorité : Haute</Badge>;
    }
    if (p === 'low') {
      return <Badge variant="secondary" className="bg-gray-100 text-gray-700 border-gray-200">Priorité : Faible</Badge>;
    }
    return <Badge className="bg-amber-100 text-amber-800 border-amber-200">Priorité : Moyenne</Badge>;
  };

  const handleComplete = async () => {
    if (onComplete) {
      await onComplete(task.id, {});
    } else {
      console.log(`Marking task ${task.id} as complete`);
    }
  };

  const handleReschedule = () => {
    console.log(`Rescheduling task ${task.id}`);
    // Implementation for rescheduling task
  };

  const handleEdit = () => {
    if (task.definitionId && onEdit) {
      onEdit(task.definitionId);
    } else {
      console.log("Missing definitionId or onEdit handler");
    }
  };

  return (
    <Card className={cn(
      "shadow-sm border-0 bg-white transition-all hover:shadow-md",
      task.status === "completed" && "opacity-75",
      task.status === "overdue" && "border-l-4 border-l-red-500"
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
                      Marquer comme terminé
                    </DropdownMenuItem>
                  )}
                  <DropdownMenuItem onClick={handleEdit}>Modifier la tâche</DropdownMenuItem>
                </DropdownMenuContent>
              </DropdownMenu>
            </div>

            {/* Task Meta Information */}
            <div className="flex flex-wrap items-center gap-3 text-sm text-gray-500">
              <div className="flex items-center gap-1">
                <Calendar className="h-4 w-4" />
                <span>
                  {task.status === 'completed' ? 'Terminé' : task.status === 'overdue' ? 'En retard' : 'À faire'}
                  {task.status === 'overdue' && ' — N\'a pas été faite'}
                </span>
              </div>

              <div className="flex items-center gap-1">
                <Clock className="h-4 w-4" />
                <span>{task.estimatedDuration && task.estimatedDuration > 0 ? `${task.estimatedDuration} min` : '—'}</span>
              </div>

              <Badge variant="outline" className="border-gray-200 text-gray-600">
                {task.room}
              </Badge>

              <span className="text-gray-400">•</span>
              <span>{task.assignee}</span>

              {/* Priority */}
              <span className="text-gray-400">•</span>
              {getPriorityBadge()}
            </div>

            {/* Status and Actions */}
            <div className="flex items-center justify-between mt-3">
              {getStatusBadge()}

              {task.status === "todo" && (
                <div className="flex gap-2">
                  <Button
                    size="sm"
                    onClick={handleComplete}
                    className="bg-blue-600 hover:bg-blue-700 text-white"
                  >
                    Terminer
                  </Button>
                </div>
              )}

              {task.status === "overdue" && (
                <div className="flex gap-2">
                  <Button size="sm" variant="outline" onClick={handleEdit} className="border-gray-200 hover:bg-gray-50">
                    Modifier la tâche
                  </Button>
                  <Button
                    size="sm"
                    onClick={handleComplete}
                    className="bg-blue-600 hover:bg-blue-700 text-white"
                  >
                    Terminer
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
