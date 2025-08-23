import React from 'react';
import { SidebarProvider, SidebarInset, SidebarTrigger } from '@/components/ui/sidebar';
import Navigation from '@/components/Navigation';
import Header from '@/components/Header';
import HouseholdSwitcher from '@/components/HouseholdSwitcher';

interface AppLayoutProps {
    children: React.ReactNode;
    activeHousehold?: string;
}

const AppLayout: React.FC<AppLayoutProps> = ({ children, activeHousehold }) => {
    return (
        <SidebarProvider>
            <Navigation />
            <SidebarInset>
                <header className="flex h-16 shrink-0 items-center gap-2 px-4 bg-white border-b border-gray-200">
                    <SidebarTrigger className="-ml-1" />
                    <div className="flex-1">
                        <div className="flex items-center justify-between">
                            <div className="flex items-center gap-4">
                                <div className="text-xl font-bold text-gray-900">HomeChores</div>
                                <HouseholdSwitcher />
                            </div>
                            <Header activeHousehold={activeHousehold} />
                        </div>
                    </div>
                </header>
                <div className="flex flex-1 flex-col p-4">
                    {children}
                </div>
            </SidebarInset>
        </SidebarProvider>
    );
};

export default AppLayout;
