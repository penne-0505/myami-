from __future__ import annotations

from bot.client import BotClient, create_client
from data.database import Database, DatabaseError
from service.points_service import PointsService
from data.repository import PointsRepository

from app.command_registry import register_commands
from app.settings import AppConfig, describe_db_settings


def create_bot_client(config: AppConfig) -> BotClient:
    diagnostics = describe_db_settings(config.db_settings)
    print(f"[startup] Supabase host: {diagnostics['supabase_host']}")
    print(f"[startup] Supabase role: {diagnostics['service_role']}")
    db = Database(
        url=config.db_settings.supabase_url,
        service_role_key=config.db_settings.service_role_key,
    )
    points_repo = PointsRepository(db)
    print("[startup] DB connection check start")
    try:
        schema_ready = db.check_connection()
    except DatabaseError as exc:
        print(f"[startup] DB connection check failed: {exc}")
        raise
    if schema_ready:
        print("[startup] DB connection OK")
    else:
        print("[startup] DB schema missing. Running setup.")
        try:
            points_repo.ensure_schema()
        except DatabaseError as exc:
            print(f"[startup] DB schema setup failed: {exc}")
            raise
        print("[startup] DB schema OK")
    client = create_client(points_repo=points_repo)
    points_service = PointsService(points_repo)
    register_commands(client, points_service=points_service)
    return client


__all__ = ["create_bot_client"]
