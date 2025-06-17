from typing import Optional, Any, List

from password_validator import PasswordValidator
from pydantic import field_validator, AnyHttpUrl
from pydantic_settings import BaseSettings
from os import path, environ


class Settings(BaseSettings):
    CORS_ORIGINS: List[AnyHttpUrl] | List[str] = None

    PROJECT_ROOT: str = path.dirname(path.dirname(path.realpath(__file__)))

    POSTGRES_USER: str
    POSTGRES_PASSWORD: str
    POSTGRES_DB: str
    POSTGRES_HOST: str
    POSTGRES_PORT: int

    SQLALCHEMY_DATABASE_URI: Optional[str] = None

    @field_validator("SQLALCHEMY_DATABASE_URI", mode="before")
    def assemble_db_connection(cls, v: Optional[str], values) -> Any:
        if isinstance(v, str):
            return v

        url = "postgresql://{}:{}@{}:{}/{}".format(
            environ.get("POSTGRES_USER"),
            environ.get("POSTGRES_PASSWORD"),
            environ.get("POSTGRES_HOST"),
            environ.get("POSTGRES_PORT"),
            environ.get("POSTGRES_DB")
        )

        return url

    PASSWORD_SCHEMA_OBJ: PasswordValidator = PasswordValidator()
    PASSWORD_SCHEMA_OBJ \
        .min(8) \
        .max(100) \
        .has().uppercase() \
        .has().lowercase() \
        .has().digits() \
        .has().no().spaces() \

    ACCESS_TOKEN_EXPIRATION_TIME: int
    REFRESH_TOKEN_EXPIRATION_TIME: int
    JWT_KEY: str

    CONST_THRESHOLD: float
    INCREASE_THRESHOLD: float
    HIGH_DOSE_THRESHOLD: float
    SATURATION_THRESHOLD: float

    SERVICE_PORT: int
    JWT_ALGORITHM: str

    # Gatekeeper info
    USING_GATEKEEPER: bool
    GATEKEEPER_BASE_URL: Optional[AnyHttpUrl] = None
    GATEKEEPER_USERNAME: str
    GATEKEEPER_PASSWORD: str
    SERVICE_NAME: str

    # Frontend
    USING_FRONTEND: bool


settings = Settings()
