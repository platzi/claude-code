from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    project_name: str = "Platziflix"
    version: str = "0.1.0"
    database_url: str = "postgresql://user:password@localhost:5432/platziflix"
    # "demo": el usuario se identifica con el header X-User-Id (solo desarrollo).
    # Cualquier otro valor deshabilita los endpoints /me hasta tener auth real.
    auth_mode: str = "demo"

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")


settings = Settings()
