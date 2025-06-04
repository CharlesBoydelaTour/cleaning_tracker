import { useState } from 'react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { useAuth } from '@/contexts/AuthContext';
import { authService } from '@/services/auth.service';

export function AuthTest() {
    const { user, isAuthenticated, logout } = useAuth();
    const [testResult, setTestResult] = useState<string>('');

    const testAuthFlow = async () => {
        try {
            // Test 1: Vérifier l'état actuel
            setTestResult('Test 1: État actuel\n');
            setTestResult(prev => prev + `- Authentifié: ${isAuthenticated}\n`);
            setTestResult(prev => prev + `- User: ${user?.email || 'Aucun'}\n\n`);

            // Test 2: Vérifier le token
            const token = localStorage.getItem('access_token');
            setTestResult(prev => prev + `Test 2: Token\n`);
            setTestResult(prev => prev + `- Token présent: ${!!token}\n`);
            if (token) {
                setTestResult(prev => prev + `- Token: ${token.substring(0, 20)}...\n\n`);
            }

            // Test 3: Appeler /auth/me
            if (isAuthenticated) {
                setTestResult(prev => prev + `Test 3: Appel /auth/me\n`);
                try {
                    const currentUser = await authService.getCurrentUser();
                    setTestResult(prev => prev + `- Succès: ${currentUser.email}\n\n`);
                } catch (error: any) {
                    setTestResult(prev => prev + `- Erreur: ${error.message}\n\n`);
                }
            }

            setTestResult(prev => prev + '✅ Tests terminés');
        } catch (error: any) {
            setTestResult(prev => prev + `\n❌ Erreur: ${error.message}`);
        }
    };

    return (
        <Card className="max-w-2xl mx-auto mt-8">
            <CardHeader>
                <CardTitle>Test d'authentification</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
                <div className="space-y-2">
                    <p><strong>État actuel:</strong></p>
                    <ul className="list-disc pl-5 text-sm">
                        <li>Authentifié: {isAuthenticated ? '✅ Oui' : '❌ Non'}</li>
                        <li>Email: {user?.email || 'N/A'}</li>
                        <li>Nom: {user?.full_name || 'N/A'}</li>
                    </ul>
                </div>

                <div className="flex gap-2">
                    <Button onClick={testAuthFlow} variant="outline">
                        Tester l'authentification
                    </Button>
                    {isAuthenticated && (
                        <Button onClick={logout} variant="destructive">
                            Se déconnecter
                        </Button>
                    )}
                </div>

                {testResult && (
                    <pre className="mt-4 p-4 bg-gray-100 rounded text-xs overflow-auto">
                        {testResult}
                    </pre>
                )}
            </CardContent>
        </Card>
    );
}