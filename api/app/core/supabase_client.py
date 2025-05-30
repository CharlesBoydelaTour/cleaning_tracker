from supabase import create_client, Client
from app.config import settings

# Client Supabase avec clé anonyme (pour l'auth côté client)
supabase: Client = create_client(settings.supabase_url, settings.supabase_anon_key)

# Client Supabase avec service role (pour les opérations côté serveur)
supabase_admin: Client = create_client(settings.supabase_url, settings.service_role_key)
