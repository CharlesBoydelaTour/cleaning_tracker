from supabase import create_client, Client
from app.config import settings

# Client Supabase avec clé anonyme (pour l'auth côté client)
supabase: Client = create_client(settings.supabase_url, settings.supabase_anon_key)

# Client Supabase admin (service role) seulement si la clé est correctement définie
supabase_admin: Client | None = None
if settings.service_role_key and not settings.service_role_key.startswith("__A_REMPLACER__"):
	supabase_admin = create_client(settings.supabase_url, settings.service_role_key)
