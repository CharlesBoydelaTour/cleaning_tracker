import asyncpg
from uuid import UUID
from typing import Optional, Dict, Any

from app.core.database import get_user_by_email, create_user, create_household_member, get_household_members
from app.schemas.member import HouseholdMember # Assurez-vous que ce schéma est approprié pour le retour

async def invite_member_to_household(
    pool: asyncpg.Pool,
    household_id: UUID,
    invitee_email: str,
    role: str,
    inviter_user_id: UUID # L\'utilisateur qui effectue l\'invitation
) -> Optional[Dict[str, Any]]:
    """
    Gère l\'invitation d\'un utilisateur à un ménage.
    1. Recherche l\'utilisateur par email.
    2. S\'il n\'existe pas, le crée (sans mot de passe, statut "pending" implicite).
    3. Vérifie s\'il est déjà membre du foyer.
    4. L\'ajoute à household_members.
    5. (Optionnel) Prépare/envoie une notification.
    """
    try:
        # 1. Rechercher l\'utilisateur par email
        user = await get_user_by_email(pool, invitee_email)

        user_id_to_add: Optional[UUID] = None

        if user:
            user_id_to_add = user["id"]
            # L'utilisateur existe déjà
            print(f"Utilisateur trouvé : {user['email']} (ID: {user['id']})")
        else:
            # 2. S'il n'existe pas, le créer
            # Le mot de passe n'est pas défini ici, l'utilisateur devra passer par un flux de confirmation/création de mot de passe
            print(f"Utilisateur non trouvé avec l'email {invitee_email}. Création en cours...")
            new_user = await create_user(pool, email=invitee_email, full_name=invitee_email.split('@')[0]) # hashed_password est None par défaut
            if new_user:
                user_id_to_add = new_user["id"]
                print(f"Nouvel utilisateur créé : {new_user['email']} (ID: {new_user['id']})")
            else:
                # La création a échoué (devrait être géré par create_user, mais double vérification)
                print(f"Échec de la création de l'utilisateur pour l'email {invitee_email}")
                return None
        
        if not user_id_to_add:
            print("Impossible de déterminer l'ID de l'utilisateur à ajouter.")
            return None

        # 3. Vérifier s'il est déjà membre du foyer
        current_members = await get_household_members(pool, household_id)
        for member in current_members:
            if member["user_id"] == user_id_to_add:
                print(f"L'utilisateur {invitee_email} (ID: {user_id_to_add}) est déjà membre du ménage {household_id}.")
                # Peut-être retourner le membre existant ou une erreur spécifique ?
                # Pour l'instant, on considère que c'est une "réussite" silencieuse ou on retourne le membre.
                # Pour être cohérent avec un ajout, on pourrait vouloir lever une exception ou retourner un code différent.
                # Ici, on retourne le membre existant pour que l'endpoint puisse le renvoyer.
                # Il faut s'assurer que le format retourné est cohérent.
                # get_household_member pourrait être plus approprié si on a l'ID du membre.
                # Pour l'instant, on retourne les détails de l'utilisateur et son rôle.
                # Il faudrait enrichir cela pour correspondre à HouseholdMember.
                # Ceci est un placeholder, la fonction create_household_member gère déjà cette logique.
                pass # La fonction create_household_member lèvera une ValueError si déjà membre.


        # 4. L'ajouter à household_members
        # La fonction create_household_member gère la vérification de l'existence et l'ajout.
        # Elle retourne le membre créé ou lève une ValueError si déjà membre.
        try:
            newly_added_member_record = await create_household_member(
                pool,
                household_id=household_id,
                user_id=user_id_to_add,
                role=role
            )
            print(f"Utilisateur {invitee_email} (ID: {user_id_to_add}) ajouté au ménage {household_id} avec le rôle {role}.")
            
            # Enrichir avec les informations de l'utilisateur si nécessaire pour correspondre au schéma de retour
            # Le schéma HouseholdMember attend id (de household_members), household_id, user_id, role, joined_at
            # create_household_member devrait retourner cela.

            # 5. (Optionnel) Préparer/envoyer une notification
            # TODO: Implémenter la logique de notification (par exemple, envoi d'email, création d'une notification en base)
            print(f"Notification d'invitation pour {invitee_email} (non implémenté).")

            return newly_added_member_record # Doit correspondre à HouseholdMember

        except ValueError as e: # Levé par create_household_member si l'utilisateur est déjà membre
            print(f"Erreur lors de l'ajout du membre (peut-être déjà membre) : {e}")
            # Si l'utilisateur est déjà membre, nous pourrions vouloir le récupérer et le retourner.
            # Pour l'instant, on laisse l'exception remonter ou on retourne None.
            # L'endpoint gère déjà les HTTPExceptions, mais ici on pourrait vouloir un comportement spécifique.
            # Pour l'instant, on retourne None, l'endpoint le traduira en 400.
            return None
        
    except Exception as e:
        print(f"Erreur inattendue dans invite_member_to_household pour {invitee_email} dans le ménage {household_id}: {e}")
        import traceback
        traceback.print_exc()
        return None

