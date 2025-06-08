import React from 'react';
import { Plus } from 'lucide-react';
import { Button } from '@/components/ui/button';

interface FloatingActionButtonProps {
    onClick: () => void;
}

export const FloatingActionButton: React.FC<FloatingActionButtonProps> = ({ onClick }) => {
    return (
        <Button
            onClick={onClick}
            className="fixed bottom-6 right-6 w-14 h-14 rounded-full shadow-lg hover:shadow-xl transition-all duration-200 z-40 md:hidden"
            size="icon"
        >
            <Plus className="w-6 h-6" />
        </Button>
    );
};

export default FloatingActionButton;