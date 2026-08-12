import os

class BackendConfig:
    PROJECT_NAME: str = "Remote Patient Monitoring with Edge AI (RPM Edge AI)"
    API_V1_STR: str = "/api/v1"
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./rpm_edge.db")
    CORS_ORIGINS: list = [
        "http://localhost:5173",
        "http://localhost:3000",
        "http://127.0.0.1:5173",
        "*"
    ]
