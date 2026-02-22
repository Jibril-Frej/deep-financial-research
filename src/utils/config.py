"""Configuration settings for the application."""

from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Configuration settings for the application."""

    EDGAR_IDENTITY: str = "default@example.com"
    TAVILY_API_KEY: str = ""
    OPENAI_API_KEY: str = ""

    DATA_DIR: Path = Path("data")
    RAW_DATA_DIR: Path = DATA_DIR / "raw"
    INDEX_DIR: Path = DATA_DIR / "index"

    # Tell Pydantic to read from the .env file at the root
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",  # Ignore extra variables in .env that aren't defined here
    )


settings = Settings()
