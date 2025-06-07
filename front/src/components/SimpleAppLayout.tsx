import React from 'react';
import Header from '@/components/Header';

interface SimpleAppLayoutProps {
    children: React.ReactNode;
    activeHousehold?: string;
}

const SimpleAppLayout: React.FC<SimpleAppLayoutProps> = ({ children, activeHousehold }) => {
    return (
        <div className="min-h-screen bg-gray-50">
            <Header activeHousehold={activeHousehold} />
            <div className="ml-64">
                {children}
            </div>
        </div>
    );
};

export default SimpleAppLayout;
