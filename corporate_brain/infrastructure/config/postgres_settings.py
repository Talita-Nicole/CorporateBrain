"""Postgres configuration loaded and validated from environment variables."""

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

DEFAULT_HOST = "localhost"
DEFAULT_PORT = 5432


class PostgresSettings(BaseSettings):
    """Postgres connection settings for session history persistence (CB-013)."""

    postgres_host: str = DEFAULT_HOST
    postgres_port: int = DEFAULT_PORT
    postgres_db: str
    postgres_user: str
    postgres_password: str

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    @field_validator("postgres_db", "postgres_user", "postgres_password")
    @classmethod
    def _required_not_empty(cls, value: str, info) -> str:
        if not value or not value.strip():
            raise ValueError(f"{info.field_name} cannot be empty")
        return value.strip()

    def connection_string(self) -> str:
        return (
            f"host={self.postgres_host} port={self.postgres_port} "
            f"dbname={self.postgres_db} user={self.postgres_user} "
            f"password={self.postgres_password}"
        )
