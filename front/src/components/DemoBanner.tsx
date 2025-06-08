import React from 'react';
import { AlertTriangle, RefreshCw } from 'lucide-react';
import { Button } from '@/components/ui/button';

interface DemoBannerProps {
    onRetry?: () => void;
}

export const DemoBanner: React.FC<DemoBannerProps> = ({ onRetry }) => {
    return (
        <div className="bg-yellow-50 border-l-4 border-yellow-400 p-4 mb-4">
            <div className="flex items-center justify-between">
                <div className="flex items-center">
                    <AlertTriangle className="h-5 w-5 text-yellow-400 mr-2" />
                    <div>
                        <p className="text-sm font-medium text-yellow-800">
                            Mode Demo
                        </p>
                        <p className="text-sm text-yellow-700">
                            Le serveur est temporairement indisponible. Données de démonstration affichées.
                        </p>
                    </div>
                </div>
                {onRetry && (
                    <Button
                        variant="outline"
                        size="sm"
                        onClick={onRetry}
                        className="ml-4"
                    >
                        <RefreshCw className="h-4 w-4 mr-1" />
                        Réessayer
                    </Button>
                )}
            </div>
        </div>
    );
};

export default DemoBanner;