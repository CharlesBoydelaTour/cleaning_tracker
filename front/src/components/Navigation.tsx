
import { Home, Calendar, BarChart3, User, Settings, Plus } from "lucide-react";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";
import {
  Sidebar,
  SidebarContent,
  SidebarGroup,
  SidebarGroupContent,
  SidebarGroupLabel,
  SidebarMenu,
  SidebarMenuButton,
  SidebarMenuItem,
  SidebarSeparator,
  SidebarHeader,
} from "@/components/ui/sidebar";
import { useLocation } from "react-router-dom";

const Navigation = () => {
  const location = useLocation();

  const navItems = [
    { icon: Home, label: "Home", path: "/", active: location.pathname === "/" },
    { icon: Calendar, label: "Calendar", path: "/calendar", active: location.pathname === "/calendar" },
    { icon: BarChart3, label: "Stats", path: "/stats", active: location.pathname === "/stats" },
    { icon: User, label: "Profile", path: "/profile", active: location.pathname === "/profile" },
    { icon: Settings, label: "Settings", path: "/settings", active: location.pathname === "/settings" },
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

      {/* Desktop Collapsible Sidebar */}
      <Sidebar variant="inset" className="hidden md:flex">
        <SidebarHeader className="border-b border-sidebar-border">
          <div className="flex items-center gap-2 px-2 py-1">
            <div className="flex aspect-square size-8 items-center justify-center rounded-lg bg-sidebar-primary text-sidebar-primary-foreground">
              <Home className="size-4" />
            </div>
            <div className="grid flex-1 text-left text-sm leading-tight">
              <span className="truncate font-semibold">HomeChores</span>
              <span className="truncate text-xs text-sidebar-muted-foreground">Navigation</span>
            </div>
          </div>
        </SidebarHeader>

        <SidebarContent>
          <SidebarGroup>
            <SidebarGroupLabel>Navigation</SidebarGroupLabel>
            <SidebarGroupContent>
              <SidebarMenu>
                {navItems.map((item) => {
                  const Icon = item.icon;
                  return (
                    <SidebarMenuItem key={item.path}>
                      <SidebarMenuButton
                        asChild
                        isActive={item.active}
                        tooltip={item.label}
                      >
                        <a href={item.path}>
                          <Icon className="h-4 w-4" />
                          <span>{item.label}</span>
                        </a>
                      </SidebarMenuButton>
                    </SidebarMenuItem>
                  );
                })}
              </SidebarMenu>
            </SidebarGroupContent>
          </SidebarGroup>

          <SidebarSeparator />

          <SidebarGroup>
            <SidebarGroupLabel>Quick Actions</SidebarGroupLabel>
            <SidebarGroupContent>
              <SidebarMenu>
                <SidebarMenuItem>
                  <SidebarMenuButton tooltip="Create Task">
                    <Plus className="h-4 w-4" />
                    <span>Create Task</span>
                  </SidebarMenuButton>
                </SidebarMenuItem>
                <SidebarMenuItem>
                  <SidebarMenuButton tooltip="Add Room">
                    <Plus className="h-4 w-4" />
                    <span>Add Room</span>
                  </SidebarMenuButton>
                </SidebarMenuItem>
              </SidebarMenu>
            </SidebarGroupContent>
          </SidebarGroup>
        </SidebarContent>
      </Sidebar>
    </>
  );
};

export default Navigation;
