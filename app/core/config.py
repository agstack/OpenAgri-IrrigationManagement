from typing import Optional, Any, List

from password_validator import PasswordValidator
from pydantic import field_validator, AnyHttpUrl
from pydantic_settings import BaseSettings
from os import path, environ

# Format: "soil_type": [default_field_capacity, wilting_point_fraction]
SOIL_WILTING_POINTS = {
    "sand": [0.12, 0.35],
    "loamy_sand": [0.16, 0.40],
    "sandy_loam": [0.22, 0.45],
    "loam": [0.30, 0.50],
    "silt_loam": [0.32, 0.50],
    "silt": [0.32, 0.50],
    "sandy_clay_loam": [0.34, 0.52],
    "clay_loam": [0.36, 0.55],
    "silty_clay_loam": [0.36, 0.55],
    "sandy_clay": [0.38, 0.58],
    "silty_clay": [0.40, 0.60],
    "clay": [0.45, 0.60],
    "peat": [0.60, 0.40],
    "chalk": [0.18, 0.45]
}

INITIAL_KC = {
    "potato": [0.5, 1.15, 0.75],
    "sugar_beet": [0.35, 1.2, 0.7]
}

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

    # Thresholds:
    RAIN_THRESHOLD_MM: float = 0.5
    FIELD_CAPACITY_WINDOW_HOURS: int = 24
    STRESS_THRESHOLD_FRACTION: float = 0.5
    LOW_DOSE_THRESHOLD_MM: float = 5.0
    HIGH_DOSE_THRESHOLD_MM: float = 20.0
    RAIN_ZERO_TOLERANCE: float = 0.01

    # Weights
    GLOBAL_WEIGHTS: dict[int, float] = {
        10: 0.15,
        20: 0.20,
        30: 0.20,
        40: 0.15,
        50: 0.15,
        60: 0.15,
    }

    SERVICE_PORT: int
    JWT_ALGORITHM: str

    # Gatekeeper info
    USING_GATEKEEPER: bool
    GATEKEEPER_BASE_URL: Optional[str] = None
    GATEKEEPER_USERNAME: str
    GATEKEEPER_PASSWORD: str
    SERVICE_NAME: str

    # Frontend
    USING_FRONTEND: bool


settings = Settings()
