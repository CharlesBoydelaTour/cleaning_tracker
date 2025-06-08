import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Home, Users, CheckCircle, ArrowRight, Sparkles } from 'lucide-react';

interface WelcomeScreenProps {
    onCreateHousehold: () => void;
}

const WelcomeScreen = ({ onCreateHousehold }: WelcomeScreenProps) => {
    return (
        <div className="container mx-auto px-4 py-12">
            <div className="max-w-4xl mx-auto text-center">
                {/* Hero Section */}
                <div className="mb-12">
                    <div className="mb-6">
                        <div className="w-20 h-20 bg-blue-100 rounded-full flex items-center justify-center mx-auto mb-4">
                            <Home className="h-10 w-10 text-blue-600" />
                        </div>
                        <h1 className="text-4xl font-bold text-gray-900 mb-4">
                            Bienvenue dans CleanTracker
                        </h1>
                        <p className="text-xl text-gray-600 max-w-2xl mx-auto">
                            Organisez et partagez les tâches ménagères avec votre famille ou vos colocataires.
                            Créez votre premier ménage pour commencer.
                        </p>
                    </div>

                    <Button
                        onClick={onCreateHousehold}
                        size="lg"
                        className="bg-blue-600 hover:bg-blue-700 text-white px-8 py-3 text-lg"
                    >
                        <Home className="h-5 w-5 mr-2" />
                        Créer mon premier ménage
                        <ArrowRight className="h-5 w-5 ml-2" />
                    </Button>
                </div>

                {/* Features Grid */}
                <div className="grid md:grid-cols-3 gap-6 mb-12">
                    <Card className="border-0 shadow-sm bg-gradient-to-br from-blue-50 to-blue-100">
                        <CardHeader className="text-center pb-3">
                            <div className="w-12 h-12 bg-blue-600 rounded-lg flex items-center justify-center mx-auto mb-3">
                                <Users className="h-6 w-6 text-white" />
                            </div>
                            <CardTitle className="text-lg font-semibold text-blue-900">
                                Collaboration
                            </CardTitle>
                        </CardHeader>
                        <CardContent className="text-center">
                            <p className="text-blue-700">
                                Invitez les membres de votre famille ou vos colocataires pour partager les responsabilités.
                            </p>
                        </CardContent>
                    </Card>

                    <Card className="border-0 shadow-sm bg-gradient-to-br from-green-50 to-green-100">
                        <CardHeader className="text-center pb-3">
                            <div className="w-12 h-12 bg-green-600 rounded-lg flex items-center justify-center mx-auto mb-3">
                                <Sparkles className="h-6 w-6 text-white" />
                            </div>
                            <CardTitle className="text-lg font-semibold text-green-900">
                                Organisation
                            </CardTitle>
                        </CardHeader>
                        <CardContent className="text-center">
                            <p className="text-green-700">
                                Créez des tâches récurrentes, assignez-les et suivez les progrès en temps réel.
                            </p>
                        </CardContent>
                    </Card>

                    <Card className="border-0 shadow-sm bg-gradient-to-br from-purple-50 to-purple-100">
                        <CardHeader className="text-center pb-3">
                            <div className="w-12 h-12 bg-purple-600 rounded-lg flex items-center justify-center mx-auto mb-3">
                                <CheckCircle className="h-6 w-6 text-white" />
                            </div>
                            <CardTitle className="text-lg font-semibold text-purple-900">
                                Suivi
                            </CardTitle>
                        </CardHeader>
                        <CardContent className="text-center">
                            <p className="text-purple-700">
                                Visualisez les statistiques et gardez votre maison propre et organisée.
                            </p>
                        </CardContent>
                    </Card>
                </div>

                {/* Getting Started Steps */}
                <Card className="max-w-2xl mx-auto bg-gray-50 border-0">
                    <CardHeader>
                        <CardTitle className="text-xl font-semibold text-gray-900">
                            Comment commencer ?
                        </CardTitle>
                    </CardHeader>
                    <CardContent>
                        <div className="space-y-4 text-left">
                            <div className="flex items-start gap-4">
                                <div className="w-8 h-8 bg-blue-600 text-white rounded-full flex items-center justify-center text-sm font-bold flex-shrink-0">
                                    1
                                </div>
                                <div>
                                    <h4 className="font-medium text-gray-900">Créez votre ménage</h4>
                                    <p className="text-gray-600 text-sm">
                                        Donnez un nom à votre ménage (famille, colocation, etc.)
                                    </p>
                                </div>
                            </div>

                            <div className="flex items-start gap-4">
                                <div className="w-8 h-8 bg-blue-600 text-white rounded-full flex items-center justify-center text-sm font-bold flex-shrink-0">
                                    2
                                </div>
                                <div>
                                    <h4 className="font-medium text-gray-900">Organisez vos pièces</h4>
                                    <p className="text-gray-600 text-sm">
                                        Ajoutez les pièces de votre logement pour mieux organiser les tâches
                                    </p>
                                </div>
                            </div>

                            <div className="flex items-start gap-4">
                                <div className="w-8 h-8 bg-blue-600 text-white rounded-full flex items-center justify-center text-sm font-bold flex-shrink-0">
                                    3
                                </div>
                                <div>
                                    <h4 className="font-medium text-gray-900">Créez vos premières tâches</h4>
                                    <p className="text-gray-600 text-sm">
                                        Définissez les tâches ménagères et leur fréquence de récurrence
                                    </p>
                                </div>
                            </div>

                            <div className="flex items-start gap-4">
                                <div className="w-8 h-8 bg-blue-600 text-white rounded-full flex items-center justify-center text-sm font-bold flex-shrink-0">
                                    4
                                </div>
                                <div>
                                    <h4 className="font-medium text-gray-900">Invitez votre famille</h4>
                                    <p className="text-gray-600 text-sm">
                                        Ajoutez d'autres membres pour partager les responsabilités
                                    </p>
                                </div>
                            </div>
                        </div>
                    </CardContent>
                </Card>
            </div>
        </div>
    );
};

export default WelcomeScreen;
