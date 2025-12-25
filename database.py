from __future__ import annotations

from typing import Any

from supabase import Client, create_client


class DatabaseError(RuntimeError):
    pass


class Database:
    def __init__(self, *, url: str, service_role_key: str):
        self._client: Client = create_client(url, service_role_key)

    @staticmethod
    def _extract_scalar(data: Any) -> Any:
        if isinstance(data, list):
            if not data:
                return None
            value = data[0]
            if isinstance(value, dict):
                if len(value) == 1:
                    return next(iter(value.values()))
                return value
            return value
        return data

    @staticmethod
    def _unwrap(response: Any, *, context: str) -> Any:
        error = getattr(response, "error", None)
        if error:
            raise DatabaseError(f"{context} failed: {error}")
        return getattr(response, "data", None)

    def ensure_schema(self) -> None:
        response = self._client.rpc("ensure_points_schema").execute()
        try:
            self._unwrap(response, context="ensure_points_schema")
        except DatabaseError as exc:
            raise DatabaseError(
                "ensure_points_schema failed. Run the SQL setup in "
                "_docs/guide/deployment/railway.md."
            ) from exc

    def ensure_user(self, user_id: int) -> None:
        response = (
            self._client.table("points")
            .upsert({"user_id": user_id, "points": 0}, on_conflict="user_id")
            .execute()
        )
        self._unwrap(response, context="ensure_user")

    def get_points(self, user_id: int) -> int | None:
        response = (
            self._client.table("points")
            .select("points")
            .eq("user_id", user_id)
            .limit(1)
            .execute()
        )
        data = self._unwrap(response, context="get_points")
        if not data:
            return None
        return int(data[0]["points"])

    def add_points(self, user_id: int, delta: int) -> int:
        response = self._client.rpc(
            "add_points", {"p_user_id": user_id, "p_delta": delta}
        ).execute()
        data = self._unwrap(response, context="add_points")
        value = self._extract_scalar(data)
        return 0 if value is None else int(value)

    def top_rank(self, limit: int = 10) -> list[dict[str, Any]]:
        response = (
            self._client.table("points")
            .select("user_id, points")
            .order("points", desc=True)
            .limit(limit)
            .execute()
        )
        data = self._unwrap(response, context="top_rank")
        return [] if data is None else list(data)

    def transfer(self, sender_id: int, recipient_id: int, points: int) -> bool:
        if points <= 0:
            return False
        response = self._client.rpc(
            "transfer_points",
            {
                "p_sender_id": sender_id,
                "p_recipient_id": recipient_id,
                "p_points": points,
            },
        ).execute()
        data = self._unwrap(response, context="transfer_points")
        value = self._extract_scalar(data)
        return bool(value)

    def has_remove_permission(self, user_id: int) -> bool:
        response = (
            self._client.table("point_remove_permissions")
            .select("user_id")
            .eq("user_id", user_id)
            .limit(1)
            .execute()
        )
        data = self._unwrap(response, context="has_remove_permission")
        return bool(data)

    def grant_remove_permission(self, user_id: int) -> None:
        response = (
            self._client.table("point_remove_permissions")
            .upsert({"user_id": user_id}, on_conflict="user_id")
            .execute()
        )
        self._unwrap(response, context="grant_remove_permission")

    def revoke_remove_permission(self, user_id: int) -> bool:
        response = (
            self._client.table("point_remove_permissions")
            .delete()
            .eq("user_id", user_id)
            .execute()
        )
        data = self._unwrap(response, context="revoke_remove_permission")
        return bool(data)

    def set_clan_register_channel(self, guild_id: int, channel_id: int) -> None:
        response = (
            self._client.table("clan_register_settings")
            .upsert({"guild_id": guild_id, "channel_id": channel_id}, on_conflict="guild_id")
            .execute()
        )
        self._unwrap(response, context="set_clan_register_channel")

    def get_clan_register_channel(self, guild_id: int) -> int | None:
        response = (
            self._client.table("clan_register_settings")
            .select("channel_id")
            .eq("guild_id", guild_id)
            .limit(1)
            .execute()
        )
        data = self._unwrap(response, context="get_clan_register_channel")
        if not data:
            return None
        return int(data[0]["channel_id"])

    def set_role_buy_price(self, guild_id: int, role_id: int, price: int) -> None:
        response = (
            self._client.table("role_buy_settings")
            .upsert(
                {"guild_id": guild_id, "role_id": role_id, "price": price},
                on_conflict="guild_id,role_id",
            )
            .execute()
        )
        self._unwrap(response, context="set_role_buy_price")

    def get_role_buy_price(self, guild_id: int, role_id: int) -> int | None:
        response = (
            self._client.table("role_buy_settings")
            .select("price")
            .eq("guild_id", guild_id)
            .eq("role_id", role_id)
            .limit(1)
            .execute()
        )
        data = self._unwrap(response, context="get_role_buy_price")
        if not data:
            return None
        return int(data[0]["price"])


class PointsRepository:
    def __init__(self, db: Database):
        self._db = db

    def ensure_schema(self) -> None:
        self._db.ensure_schema()

    def ensure_user(self, user_id: int) -> None:
        self._db.ensure_user(user_id)

    def get_points(self, user_id: int) -> int | None:
        return self._db.get_points(user_id)

    def add_points(self, user_id: int, delta: int) -> int:
        return self._db.add_points(user_id, delta)

    def top_rank(self, limit: int = 10) -> list[dict[str, Any]]:
        return self._db.top_rank(limit)

    def transfer(self, sender_id: int, recipient_id: int, points: int) -> bool:
        return self._db.transfer(sender_id, recipient_id, points)

    def award_point_for_message(self, user_id: int) -> int:
        return self.add_points(user_id, 1)

    def get_user_points(self, user_id: int) -> int | None:
        return self.get_points(user_id)

    def get_top_rank(self, limit: int = 10) -> list[dict[str, Any]]:
        return self.top_rank(limit)

    def send_points(self, sender_id: int, recipient_id: int, points: int) -> bool:
        return self.transfer(sender_id, recipient_id, points)

    def remove_points(self, admin_id: int, target_id: int, points: int) -> bool:
        return self.transfer(target_id, admin_id, points)

    def has_remove_permission(self, user_id: int) -> bool:
        return self._db.has_remove_permission(user_id)

    def grant_remove_permission(self, user_id: int) -> None:
        self._db.grant_remove_permission(user_id)

    def revoke_remove_permission(self, user_id: int) -> bool:
        return self._db.revoke_remove_permission(user_id)

    def set_clan_register_channel(self, guild_id: int, channel_id: int) -> None:
        self._db.set_clan_register_channel(guild_id, channel_id)

    def get_clan_register_channel(self, guild_id: int) -> int | None:
        return self._db.get_clan_register_channel(guild_id)

    def set_role_buy_price(self, guild_id: int, role_id: int, price: int) -> None:
        self._db.set_role_buy_price(guild_id, role_id, price)

    def get_role_buy_price(self, guild_id: int, role_id: int) -> int | None:
        return self._db.get_role_buy_price(guild_id, role_id)
