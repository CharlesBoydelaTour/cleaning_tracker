import React from 'react';
import { ChevronDown, User, LogOut, Mail } from 'lucide-react';
import { Button } from '@/components/ui/button';
import {
    DropdownMenu,
    DropdownMenuContent,
    DropdownMenuItem,
    DropdownMenuSeparator,
    DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';
import { useAuth } from '@/contexts/AuthContext';
import { Link } from 'react-router-dom';

const HeaderUserMenu: React.FC = () => {
    const { user, logout } = useAuth();

    return (
        <DropdownMenu>
            <DropdownMenuTrigger asChild>
                <Button variant="ghost" className="flex items-center gap-2">
                    <User className="h-4 w-4" />
                    <span className="hidden md:inline">{user?.email}</span>
                    <ChevronDown className="h-4 w-4" />
                </Button>
            </DropdownMenuTrigger>
            <DropdownMenuContent align="end" className="w-48">
                <div className="px-2 py-1.5">
                    <p className="text-sm text-gray-600">{user?.email}</p>
                    {user && !user.email_confirmed_at && (
                        <p className="text-xs text-yellow-600 mt-1 flex items-center gap-1">
                            <Mail className="h-3 w-3" />
                            Email non vérifié
                        </p>
                    )}
                </div>
                <DropdownMenuSeparator />

                <DropdownMenuItem asChild>
                    <Link to="/profile" className="flex items-center gap-2">
                        <User className="h-4 w-4" />
                        Profile
                    </Link>
                </DropdownMenuItem>
                <DropdownMenuItem
                    onClick={logout}
                    className="flex items-center gap-2 text-red-600 focus:text-red-600"
                >
                    <LogOut className="h-4 w-4" />
                    Logout
                </DropdownMenuItem>
            </DropdownMenuContent>
        </DropdownMenu>
    );
};

export default HeaderUserMenu;
