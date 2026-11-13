from typing import List, Union
from pydantic import AnyHttpUrl, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    PROJECT_NAME: str = "AI-Driven Micro-Grid Load Balancing & Solar Forecasting"
    API_V1_STR: str = "/api/v1"
    
    # Database
    DATABASE_URL: str = "sqlite:///./microgrid.db"
    
    # Authentication & JWT
    JWT_SECRET: str = "dev_super_secret_jwt_key_microgrid_2026_change_in_production"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24  # 24 hours
    
    # CORS
    CORS_ORIGINS: Union[List[str], str] = [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:8000",
        "http://127.0.0.1:8000",
    ]
    
    # Demo & Simulation
    DEMO_MODE: bool = True
    SIMULATION_REFRESH_SECONDS: int = 10
    AI_SERVICE_URL: str = "http://127.0.0.1:8100"
    AI_SERVICE_TIMEOUT_SECONDS: float = 30.0
    AI_SIMULATION_START_TIME: str = "2019-01-08T00:00:00Z"
    
    # Default Seed Credentials
    DEFAULT_ADMIN_EMAIL: str = "admin@microgrid.io"
    DEFAULT_ADMIN_PASSWORD: str = "Admin@12345"
    DEFAULT_OPERATOR_EMAIL: str = "operator@microgrid.io"
    DEFAULT_OPERATOR_PASSWORD: str = "Operator@12345"
    DEFAULT_ANALYST_EMAIL: str = "analyst@microgrid.io"
    DEFAULT_ANALYST_PASSWORD: str = "Analyst@12345"

    @field_validator("CORS_ORIGINS", mode="before")
    def assemble_cors_origins(cls, v: Union[str, List[str]]) -> List[str]:
        if isinstance(v, str) and not v.startswith("["):
            return [i.strip() for i in v.split(",") if i.strip()]
        elif isinstance(v, list):
            return v
        return ["*"]

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore"
    )


settings = Settings()
