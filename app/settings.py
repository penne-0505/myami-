from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from urllib.parse import urlparse
import base64
import json
import os

from dotenv import load_dotenv

from app.config import load_token


@dataclass(frozen=True, slots=True)
class DBSettings:
    supabase_url: str
    service_role_key: str


@dataclass(frozen=True, slots=True)
class DiscordSettings:
    secret_token: str


@dataclass(frozen=True, slots=True)
class AppConfig:
    db_settings: DBSettings
    discord_settings: DiscordSettings


def _load_env_file(env_file: str | Path | None = None) -> None:
    if env_file is None:
        load_dotenv()
    else:
        path = Path(env_file)
        load_dotenv(dotenv_path=path)


def _get_jwt_role(token: str) -> str | None:
    parts = token.split(".")
    if len(parts) < 2:
        return None
    payload = parts[1]
    padding = "=" * (-len(payload) % 4)
    try:
        decoded = base64.urlsafe_b64decode(payload + padding)
        data = json.loads(decoded.decode("utf-8"))
    except (ValueError, json.JSONDecodeError):
        return None
    role = data.get("role")
    return role if isinstance(role, str) else None


def describe_db_settings(db_settings: DBSettings) -> dict[str, str | None]:
    parsed = urlparse(db_settings.supabase_url)
    host = parsed.hostname or ""
    return {
        "supabase_host": host,
        "service_role": _get_jwt_role(db_settings.service_role_key),
    }


def load_discord_settings(
    raw_token: str | None = None,
) -> DiscordSettings:
    token = raw_token if raw_token is not None else load_token()
    if token is None or token.strip() == "":
        raise ValueError("Discord secret token is not provided.")
    secret_token = token.strip()
    return DiscordSettings(secret_token=secret_token)


def load_db_settings(
    raw_supabase_url: str | None = None, raw_service_role_key: str | None = None
) -> DBSettings:
    supabase_url = (
        raw_supabase_url if raw_supabase_url is not None else os.getenv("SUPABASE_URL")
    )
    supabase_url = supabase_url.strip() if supabase_url is not None else ""
    if supabase_url == "":
        raise ValueError("SUPABASE_URL is not provided.")

    service_role_key = (
        raw_service_role_key
        if raw_service_role_key is not None
        else os.getenv("SUPABASE_SERVICE_ROLE_KEY")
    )
    service_role_key = service_role_key.strip() if service_role_key is not None else ""
    if service_role_key == "":
        raise ValueError("SUPABASE_SERVICE_ROLE_KEY is not provided.")
    role = _get_jwt_role(service_role_key)
    if role is None:
        raise ValueError("SUPABASE_SERVICE_ROLE_KEY is invalid or missing role claim.")
    if role != "service_role":
        raise ValueError(
            "SUPABASE_SERVICE_ROLE_KEY must be a service_role key, "
            f"but role was '{role}'."
        )

    return DBSettings(supabase_url=supabase_url, service_role_key=service_role_key)


def load_config(env_file: str | Path | None = None) -> AppConfig:
    _load_env_file(env_file)
    discord_settings = load_discord_settings()
    db_settings = load_db_settings()
    return AppConfig(db_settings=db_settings, discord_settings=discord_settings)


__all__ = [
    "AppConfig",
    "DBSettings",
    "DiscordSettings",
    "describe_db_settings",
    "load_config",
    "load_db_settings",
    "load_discord_settings",
]
