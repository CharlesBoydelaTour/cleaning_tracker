import { useState } from 'react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import apiClient from '@/lib/api-client';

export function ApiTest() {
    const [status, setStatus] = useState<'idle' | 'loading' | 'success' | 'error'>('idle');
    const [data, setData] = useState<any>(null);
    const [error, setError] = useState<string | null>(null);

    const testConnection = async () => {
        setStatus('loading');
        setError(null);

        try {
            console.log('Testing API connection...');
            const response = await apiClient.get('/');
            console.log('API Response:', response);
            setData(response.data);
            setStatus('success');
        } catch (err: any) {
            console.error('API Error:', err);
            console.error('Error response:', err.response);
            console.error('Error message:', err.message);

            let errorMessage = 'Connection failed';
            if (err.response) {
                errorMessage = `Server error ${err.response.status}: ${err.response.statusText}`;
                if (err.response.data) {
                    errorMessage += ` - ${JSON.stringify(err.response.data)}`;
                }
            } else if (err.request) {
                errorMessage = `Network error: Request was made but no response received. Check if API is running on the correct port.`;
            } else {
                errorMessage = `Request setup error: ${err.message}`;
            }

            setError(errorMessage);
            setStatus('error');
        }
    };

    return (
        <Card className="max-w-md mx-auto mt-8">
            <CardHeader>
                <CardTitle>Test de connexion API</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
                <Button
                    onClick={testConnection}
                    disabled={status === 'loading'}
                    className="w-full"
                >
                    {status === 'loading' ? 'Test en cours...' : 'Tester la connexion'}
                </Button>

                {status === 'success' && (
                    <div className="p-4 bg-green-50 text-green-800 rounded">
                        <p className="font-semibold">✅ Connexion réussie!</p>
                        <pre className="text-xs mt-2">{JSON.stringify(data, null, 2)}</pre>
                    </div>
                )}

                {status === 'error' && (
                    <div className="p-4 bg-red-50 text-red-800 rounded">
                        <p className="font-semibold">❌ Erreur de connexion</p>
                        <p className="text-sm mt-1">{error}</p>
                    </div>
                )}
            </CardContent>
        </Card>
    );
}