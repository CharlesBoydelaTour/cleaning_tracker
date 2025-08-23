import React from 'react';
import { ChevronDown, Home } from 'lucide-react';
import { Button } from '@/components/ui/button';
import {
    DropdownMenu,
    DropdownMenuContent,
    DropdownMenuItem,
    DropdownMenuLabel,
    DropdownMenuSeparator,
    DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';
import { useCurrentHousehold } from '@/hooks/use-current-household';
import { Link } from 'react-router-dom';

export default function HouseholdSwitcher() {
    const {
        currentHousehold,
        households,
        selectHousehold,
    } = useCurrentHousehold();

    const activeName = currentHousehold?.name || 'Foyer';

    return (
        <DropdownMenu>
            <DropdownMenuTrigger asChild>
                <Button variant="ghost" className="flex items-center gap-2 text-sm text-gray-700">
                    <Home className="h-4 w-4" />
                    <span className="max-w-[180px] truncate">{activeName}</span>
                    <ChevronDown className="h-4 w-4" />
                </Button>
            </DropdownMenuTrigger>
            <DropdownMenuContent align="start" className="w-64">
                <DropdownMenuLabel>Mes foyers</DropdownMenuLabel>
                <DropdownMenuSeparator />
                {households && households.length > 0 ? (
                    households.map((h) => (
                        <DropdownMenuItem
                            key={h.id}
                            onClick={() => selectHousehold(h.id)}
                            className="cursor-pointer"
                        >
                            <div className="flex items-center gap-2">
                                <div className="h-6 w-6 rounded bg-blue-100 text-blue-700 flex items-center justify-center">
                                    <Home className="h-3.5 w-3.5" />
                                </div>
                                <span className="truncate">{h.name}</span>
                            </div>
                        </DropdownMenuItem>
                    ))
                ) : (
                    <div className="px-2 py-2 text-sm text-gray-500">Aucun foyer</div>
                )}
                <DropdownMenuSeparator />
                <DropdownMenuItem asChild>
                    <Link to="/households" className="text-blue-600">Gérer les foyers</Link>
                </DropdownMenuItem>
            </DropdownMenuContent>
        </DropdownMenu>
    );
}
