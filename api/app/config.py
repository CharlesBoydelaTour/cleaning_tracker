from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional


class Settings(BaseSettings):
    database_url: str  # Pydantic cherchera DATABASE_URL (insensible à la casse)
    secret_key: str  # Pydantic cherchera SECRET_KEY (insensible à la casse)
    redis_url: str  # Variable dans .env
    service_role_key: str  # Pydantic cherchera SERVICE_ROLE_KEY (insensible à la casse)

    # Supabase settings
    supabase_url: str  # URL de votre projet Supabase
    supabase_anon_key: str  # Clé publique anon

    # JWT settings
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    refresh_token_expire_days: int = 7

    # Propriété dérivée pour celery_broker_url
    @property
    def celery_broker_url(self) -> str:
        return self.redis_url

    # Add other settings as needed

    model_config = SettingsConfigDict(
        env_file=".env",  # Chemin relatif depuis la racine du projet
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    # Logging settings
    environment: str = "development"  # development, staging, production
    log_level: str = "INFO"  # DEBUG, INFO, WARNING, ERROR, CRITICAL
    log_format: str = "text"  # text, json
    log_file_path: Optional[str] = (
        "logs/app.log"  # None pour désactiver les logs fichier
    )
    log_max_bytes: int = 10485760
    log_backup_count: int = 5  # Nombre de fichiers de backup à conserver

    # SMTP settings pour les emails
    smtp_host: str = "smtp.gmail.com"
    smtp_port: int = 587
    smtp_user: Optional[str] = None
    smtp_password: Optional[str] = None
    sender_email: str = "noreply@cleaningtracker.com"
    sender_name: str = "Cleaning Tracker"
    
    # URL de l'application (pour les liens dans les emails)
    app_url: str = "https://cleaningtracker.com"
    
    # Expo push notifications
    expo_access_token: Optional[str] = None

settings = Settings()
