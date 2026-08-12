import os

class Settings:
    """Centralized System Configuration & Security Environment Variables Manager."""
    PROJECT_NAME: str = "Remote Patient Monitoring with Edge AI"
    VERSION: str = "1.0.0"
    
    # Database Configuration (SQLite dev default, PostgreSQL compatible)
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./rpm_edge_ai.db")
    
    # Security Secrets (Override in production via environment variable SECRET_KEY)
    SECRET_KEY: str = os.getenv("SECRET_KEY", "09d25e094faa6ca2556c818166b7a9563b93f7099f6f0f4caa6cf63b88e8d3e7")
    ALGORITHM: str = os.getenv("ALGORITHM", "HS256")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))
    
    # Security Aliases for JWT Module Compatibility
    @property
    def JWT_SECRET_KEY(self) -> str:
        return self.SECRET_KEY

    @property
    def JWT_ALGORITHM(self) -> str:
        return self.ALGORITHM

    # Rate Limiting Configuration
    LOGIN_RATE_LIMIT_PER_MINUTE: int = int(os.getenv("LOGIN_RATE_LIMIT_PER_MINUTE", "10"))
    
    # CORS Configuration
    CORS_ORIGINS: list = os.getenv("CORS_ORIGINS", "*").split(",")

settings = Settings()
