import { useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Avatar, AvatarFallback } from "@/components/ui/avatar";
import { MoreHorizontal, Shield, User, Eye, UserMinus } from "lucide-react";
import { DropdownMenu, DropdownMenuContent, DropdownMenuItem, DropdownMenuTrigger } from "@/components/ui/dropdown-menu";
import { HouseholdMember } from "@/types/household.types";

interface MemberCardProps {
    member: HouseholdMember & {
        user_name?: string;
        user_email?: string;
    };
    currentUserId?: string;
    currentUserRole?: string;
    onRoleChange: (memberId: string, newRole: 'admin' | 'member' | 'guest') => void;
    onRemoveMember: (memberId: string) => void;
    isUpdating?: boolean;
}

const MemberCard = ({
    member,
    currentUserId,
    currentUserRole,
    onRoleChange,
    onRemoveMember,
    isUpdating = false
}: MemberCardProps) => {
    const [isChangingRole, setIsChangingRole] = useState(false);

    const isCurrentUser = member.user_id === currentUserId;
    const canManageMembers = currentUserRole === 'admin';
    const canChangeRole = canManageMembers && !isCurrentUser;
    const canRemove = canManageMembers && !isCurrentUser;

    const roleIconsSafe = {
        admin: Shield,
        member: User,
        guest: Eye
    };

    const roleLabelsSafe = {
        admin: 'Administrateur',
        member: 'Membre',
        guest: 'Invité'
    };

    // Utiliser des fallbacks plus robustes pour RoleIcon et currentRoleLabel
    const RoleIcon = roleIconsSafe[member.role as keyof typeof roleIconsSafe] || User; 
    const currentRoleLabel = roleLabelsSafe[member.role as keyof typeof roleLabelsSafe] || 'Membre';

    const roleColors = {
        admin: 'bg-red-100 text-red-800 border-red-200',
        member: 'bg-blue-100 text-blue-800 border-blue-200',
        guest: 'bg-gray-100 text-gray-800 border-gray-200'
    };

    const handleRoleChange = (newRole: 'admin' | 'member' | 'guest') => {
        setIsChangingRole(true);
        onRoleChange(member.id, newRole);
        // Note: isChangingRole sera remis à false quand le parent se mettra à jour
    };

    const handleRemove = () => {
        if (confirm(`Êtes-vous sûr de vouloir retirer ${member.user_name || member.user_email} du foyer ?`)) {
            onRemoveMember(member.id);
        }
    };

    const getInitials = (name?: string, email?: string) => {
        if (name) {
            return name.split(' ').map(n => n[0]).join('').toUpperCase().slice(0, 2);
        }
        if (email) {
            return email.slice(0, 2).toUpperCase();
        }
        return 'U';
    };

    return (
        <Card className="hover:shadow-md transition-shadow">
            <CardContent className="p-4">
                <div className="flex items-center justify-between">
                    <div className="flex items-center gap-3">
                        <Avatar className="h-10 w-10">
                            <AvatarFallback className="bg-blue-100 text-blue-600">
                                {getInitials(member.user_name, member.user_email)}
                            </AvatarFallback>
                        </Avatar>

                        <div className="flex-1">
                            <div className="flex items-center gap-2">
                                <h3 className="font-medium text-gray-900">
                                    {member.user_name || member.user_email}
                                    {isCurrentUser && <span className="text-sm text-gray-500">(Vous)</span>}
                                </h3>
                            </div>
                            {member.user_name && member.user_email && (
                                <p className="text-sm text-gray-600">{member.user_email}</p>
                            )}
                            <p className="text-xs text-gray-500">
                                {member.joined_at ? `Membre depuis ${new Date(member.joined_at).toLocaleDateString('fr-FR')}` : 'Date d\'adhésion inconnue'}
                            </p>
                        </div>
                    </div>

                    <div className="flex items-center gap-2">
                        {canChangeRole ? (
                            <Select
                                value={member.role}
                                onValueChange={handleRoleChange}
                                disabled={isChangingRole || isUpdating}
                            >
                                <SelectTrigger className="w-32">
                                    <div className="flex items-center gap-1">
                                        <RoleIcon className="h-3 w-3" />
                                        <span className="text-xs">{currentRoleLabel}</span>
                                    </div>
                                </SelectTrigger>
                                <SelectContent>
                                    {Object.entries(roleLabelsSafe).map(([value, label]) => {
                                        // S'assurer que ItemIcon a un fallback
                                        const ItemIcon = roleIconsSafe[value as keyof typeof roleIconsSafe] || User;
                                        return (
                                            <SelectItem key={value} value={value}>
                                                <div className="flex items-center gap-2">
                                                    <ItemIcon className="h-3 w-3" />
                                                    <span>{label}</span>
                                                </div>
                                            </SelectItem>
                                        );
                                    })}
                                </SelectContent>
                            </Select>
                        ) : (
                            <Badge variant="secondary" className={roleColors[member.role as keyof typeof roleColors] || roleColors.member}>
                                <RoleIcon className="h-3 w-3 mr-1" />
                                {currentRoleLabel}
                            </Badge>
                        )}

                        {canRemove && (
                            <DropdownMenu>
                                <DropdownMenuTrigger asChild>
                                    <Button variant="ghost" size="sm">
                                        <MoreHorizontal className="h-4 w-4" />
                                    </Button>
                                </DropdownMenuTrigger>
                                <DropdownMenuContent align="end">
                                    <DropdownMenuItem
                                        onClick={handleRemove}
                                        className="text-red-600 focus:text-red-600"
                                    >
                                        <UserMinus className="h-4 w-4 mr-2" />
                                        Retirer du foyer
                                    </DropdownMenuItem>
                                </DropdownMenuContent>
                            </DropdownMenu>
                        )}
                    </div>
                </div>
            </CardContent>
        </Card>
    );
};

export default MemberCard;
