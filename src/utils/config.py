from pathlib import Path
import os

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parents[2]
DOTENV_PATH = BASE_DIR / ".env"

load_dotenv(dotenv_path=DOTENV_PATH, override=False)

REQUIRED_ENV_VARS = [
    "ADZUNA_APP_ID",
    "ADZUNA_APP_KEY",
    "AZURE_STORAGE_CONNECTION_STRING",
    "SQL_SERVER",
    "SQL_DATABASE",
    "SQL_USERNAME",
    "SQL_PASSWORD",
]


class ConfigError(Exception):
    pass


def get_env_variable(name: str) -> str:
    value = os.getenv(name)
    if value is None or value.strip() == "":
        raise ConfigError(f"Required environment variable '{name}' is missing or empty.")
    return value


def get_required_config() -> dict[str, str]:
    return {name: get_env_variable(name) for name in REQUIRED_ENV_VARS}


def get_optional_env_variable(name: str, default: str | None = None) -> str | None:
    value = os.getenv(name)
    if value is None or value.strip() == "":
        return default
    return value
