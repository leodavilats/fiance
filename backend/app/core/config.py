from __future__ import annotations

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict

DEFAULT_JWT_SECRET = "change-me"
DEFAULT_WEBHOOK_SECRET = "segredo-de-desenvolvimento"


class InsecureConfigurationError(RuntimeError):
    pass


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_env: str = ""

    log_level: str = "INFO"

    allowed_origins: str = "http://localhost:4200,http://127.0.0.1:4200"

    database_url: str = "sqlite:///./.cache/fiance.db"

    google_client_id: str = ""

    jwt_secret: str = DEFAULT_JWT_SECRET

    admin_user_ids: str = ""

    rate_limit_enabled: bool = True

    rate_limit_factor: float = 1.0

    trusted_proxy_count: int = 0

    entitlements_enabled: bool = False

    affirmation_level: int = 2

    suitability_personalization_allowed: bool = False

    billing_webhook_secret: str = DEFAULT_WEBHOOK_SECRET

    brapi_token: str = ""

    brapi_history_range: str = "3mo"

    firebase_service_account_json: str = ""

    @property
    def is_development(self) -> bool:
        return self.app_env.strip().lower() == "development"

    @property
    def cors_origins(self) -> list[str]:
        if self.is_development:
            return ["*"]
        return [o.strip() for o in self.allowed_origins.split(",") if o.strip()]

    @property
    def cors_allow_credentials(self) -> bool:
        return "*" not in self.cors_origins

    def validate_for_startup(self) -> None:
        if not self.app_env.strip():
            raise InsecureConfigurationError(
                "APP_ENV não definido. Declare explicitamente 'development' ou "
                "'production' — sem isso não há como saber se o segredo de JWT, a "
                "origem de CORS e a rota de operador estão configurados para valer."
            )

        if self.is_development:
            return

        if self.jwt_secret == DEFAULT_JWT_SECRET or not self.jwt_secret.strip():
            raise InsecureConfigurationError(
                "JWT_SECRET não configurado (ainda está no valor default 'change-me'). "
                f"Defina JWT_SECRET no ambiente antes de subir com APP_ENV={self.app_env!r}."
            )

        if not self.cors_origins:
            raise InsecureConfigurationError(
                "ALLOWED_ORIGINS vazio fora de development — nenhuma origem poderia "
                "consumir a API. Configure ALLOWED_ORIGINS."
            )

        if (
            self.billing_webhook_secret == DEFAULT_WEBHOOK_SECRET
            or not self.billing_webhook_secret.strip()
        ):
            raise InsecureConfigurationError(
                "BILLING_WEBHOOK_SECRET não configurado (ainda está no valor default "
                "versionado no repositório). Defina BILLING_WEBHOOK_SECRET antes de "
                f"subir com APP_ENV={self.app_env!r}."
            )

    @property
    def admin_ids(self) -> list[str]:
        return [a.strip() for a in self.admin_user_ids.split(",") if a.strip()]

    @property
    def google_client_ids(self) -> list[str]:
        return [c.strip() for c in self.google_client_id.split(",") if c.strip()]

    @property
    def sqlalchemy_database_url(self) -> str:
        url = self.database_url or "sqlite:///./.cache/fiance.db"
        if url.startswith("postgres://"):
            url = "postgresql+psycopg://" + url[len("postgres://") :]
        elif url.startswith("postgresql://"):
            url = "postgresql+psycopg://" + url[len("postgresql://") :]
        return url


@lru_cache
def get_settings() -> Settings:

    return Settings()
