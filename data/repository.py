from data.database import Database


from typing import Any


class PointsRepository:
    def __init__(self, db: Database):
        self._db = db

    def ensure_schema(self) -> None:
        self._db.ensure_schema()

    def ensure_user(self, guild_id: int, user_id: int) -> None:
        self._db.ensure_user(guild_id, user_id)

    def get_points(self, guild_id: int, user_id: int) -> int | None:
        return self._db.get_points(guild_id, user_id)

    def add_points(self, guild_id: int, user_id: int, delta: int) -> int:
        return self._db.add_points(guild_id, user_id, delta)

    def top_rank(self, guild_id: int, limit: int = 10) -> list[dict[str, Any]]:
        return self._db.top_rank(guild_id, limit)

    def transfer(
        self, guild_id: int, sender_id: int, recipient_id: int, points: int
    ) -> bool:
        return self._db.transfer(guild_id, sender_id, recipient_id, points)

    def award_point_for_message(self, guild_id: int, user_id: int) -> int:
        return self.add_points(guild_id, user_id, 1)

    def get_user_points(self, guild_id: int, user_id: int) -> int | None:
        return self.get_points(guild_id, user_id)

    def get_top_rank(self, guild_id: int, limit: int = 10) -> list[dict[str, Any]]:
        return self.top_rank(guild_id, limit)

    def send_points(
        self, guild_id: int, sender_id: int, recipient_id: int, points: int
    ) -> bool:
        return self.transfer(guild_id, sender_id, recipient_id, points)

    def remove_points(
        self, guild_id: int, admin_id: int, target_id: int, points: int
    ) -> bool:
        return self.transfer(guild_id, target_id, admin_id, points)

    def has_remove_permission(self, guild_id: int, user_id: int) -> bool:
        return self._db.has_remove_permission(guild_id, user_id)

    def grant_remove_permission(self, guild_id: int, user_id: int) -> None:
        self._db.grant_remove_permission(guild_id, user_id)

    def revoke_remove_permission(self, guild_id: int, user_id: int) -> bool:
        return self._db.revoke_remove_permission(guild_id, user_id)

    def set_clan_register_channel(self, guild_id: int, channel_id: int) -> None:
        self._db.set_clan_register_channel(guild_id, channel_id)

    def get_clan_register_channel(self, guild_id: int) -> int | None:
        return self._db.get_clan_register_channel(guild_id)

    def set_role_buy_price(self, guild_id: int, role_id: int, price: int) -> None:
        self._db.set_role_buy_price(guild_id, role_id, price)

    def get_role_buy_price(self, guild_id: int, role_id: int) -> int | None:
        return self._db.get_role_buy_price(guild_id, role_id)


__all__ = ["PointsRepository"]
