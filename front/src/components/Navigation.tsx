
import { Home, Calendar, BarChart3, User, Settings } from "lucide-react";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";

const Navigation = () => {
  const navItems = [
    { icon: Home, label: "Home", path: "/", active: true },
    { icon: Calendar, label: "Calendar", path: "/calendar", active: false },
    { icon: BarChart3, label: "Stats", path: "/stats", active: false },
    { icon: User, label: "Profile", path: "/profile", active: false },
    { icon: Settings, label: "Settings", path: "/settings", active: false },
  ];

  return (
    <>
      {/* Mobile Bottom Navigation */}
      <nav className="fixed bottom-0 left-0 right-0 bg-white border-t border-gray-200 md:hidden z-40">
        <div className="flex items-center justify-around h-16 px-2">
          {navItems.map((item) => {
            const Icon = item.icon;
            return (
              <Button
                key={item.path}
                variant="ghost"
                size="sm"
                className={cn(
                  "flex flex-col items-center justify-center h-12 w-12 p-0 gap-1",
                  item.active ? "text-blue-600" : "text-gray-400"
                )}
              >
                <Icon className="h-5 w-5" />
                <span className="text-xs">{item.label}</span>
              </Button>
            );
          })}
        </div>
      </nav>

      {/* Desktop Side Navigation */}
      <nav className="hidden md:flex fixed left-0 top-16 bottom-0 w-64 bg-white border-r border-gray-200 z-40">
        <div className="flex flex-col w-full p-4 space-y-2">
          <div className="mb-4">
            <h2 className="text-sm font-semibold text-gray-500 uppercase tracking-wide mb-2">
              Navigation
            </h2>
          </div>
          
          {navItems.map((item) => {
            const Icon = item.icon;
            return (
              <Button
                key={item.path}
                variant={item.active ? "secondary" : "ghost"}
                className={cn(
                  "w-full justify-start gap-3 h-10",
                  item.active 
                    ? "bg-blue-50 text-blue-700 border-blue-200" 
                    : "text-gray-600 hover:bg-gray-50"
                )}
              >
                <Icon className="h-5 w-5" />
                {item.label}
              </Button>
            );
          })}
          
          <div className="pt-4 mt-4 border-t border-gray-200">
            <h3 className="text-sm font-semibold text-gray-500 uppercase tracking-wide mb-2">
              Quick Actions
            </h3>
            <Button 
              variant="outline" 
              className="w-full justify-start gap-3 h-10 border-gray-200 hover:bg-gray-50"
            >
              <Home className="h-5 w-5" />
              Create Task
            </Button>
            <Button 
              variant="outline" 
              className="w-full justify-start gap-3 h-10 mt-2 border-gray-200 hover:bg-gray-50"
            >
              <Calendar className="h-5 w-5" />
              Add Room
            </Button>
          </div>
        </div>
      </nav>
    </>
  );
};

export default Navigation;
