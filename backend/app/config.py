import os

from dotenv import load_dotenv

# Loads backend/.env (git-ignored) so OPENAI_API_KEY / ANTHROPIC_API_KEY etc. can live there.
load_dotenv()


class Settings:
    """Application settings, sourced from environment variables (.env)."""

    app_name: str = "Hanwha Qcells L1 Assistant API"
    app_description: str = (
        "Backend API for the Hanwha Qcells L1 Assistant — a support chatbot for "
        "solar installers and admins. Handles auth, knowledge-base-grounded chat, "
        "agent handoff, feedback/ratings, and the admin dashboard."
    )
    app_version: str = "0.1.0"
    api_prefix: str = "/api"

    cors_origins: list[str] = [
        origin.strip()
        for origin in os.getenv("CORS_ORIGINS", "http://localhost:3000").split(",")
        if origin.strip()
    ]


settings = Settings()
