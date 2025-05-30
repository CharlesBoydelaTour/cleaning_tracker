from pydantic_settings import BaseSettings, SettingsConfigDict


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


settings = Settings()
