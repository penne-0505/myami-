from __future__ import annotations

from dataclasses import dataclass

from service.repository import PointsRepository


class PointsServiceError(Exception):
    """Base exception for points service errors."""


class InvalidPointsError(PointsServiceError):
    pass


class PermissionDeniedError(PointsServiceError):
    pass


class InsufficientPointsError(PointsServiceError):
    pass


class TargetHasNoPointsError(PointsServiceError):
    pass


class OperationFailedError(PointsServiceError):
    pass


class MissingClanRegisterChannelError(PointsServiceError):
    pass


class RoleNotForSaleError(PointsServiceError):
    pass


class PermissionNotGrantedError(PointsServiceError):
    pass


@dataclass(frozen=True, slots=True)
class RolePurchase:
    role_id: int
    price: int


def _require_positive_points(points: int) -> None:
    if points <= 0:
        raise InvalidPointsError("points must be positive")


class PointsService:
    def __init__(self, repo: PointsRepository) -> None:
        self._repo = repo

    def get_user_points(self, guild_id: int, user_id: int) -> int | None:
        return self._repo.get_user_points(guild_id, user_id)

    def get_top_rank(self, guild_id: int, limit: int = 10) -> list[dict]:
        return self._repo.get_top_rank(guild_id, limit)

    def send_points(
        self,
        guild_id: int,
        sender_id: int,
        recipient_id: int,
        points: int,
    ) -> None:
        _require_positive_points(points)
        success = self._repo.send_points(guild_id, sender_id, recipient_id, points)
        if not success:
            raise InsufficientPointsError("insufficient points")

    def remove_points(
        self,
        guild_id: int,
        admin_id: int,
        target_id: int,
        points: int,
        *,
        is_admin: bool,
    ) -> None:
        _require_positive_points(points)
        if not is_admin and not self._repo.has_remove_permission(guild_id, admin_id):
            raise PermissionDeniedError("remove permission is required")
        target_points = self._repo.get_user_points(guild_id, target_id)
        if target_points is None:
            raise TargetHasNoPointsError("target has no points")
        if target_points < points:
            raise InsufficientPointsError("target has insufficient points")
        success = self._repo.remove_points(guild_id, admin_id, target_id, points)
        if not success:
            raise OperationFailedError("remove points failed")

    def grant_remove_permission(self, guild_id: int, user_id: int) -> None:
        self._repo.grant_remove_permission(guild_id, user_id)

    def revoke_remove_permission(self, guild_id: int, user_id: int) -> None:
        removed = self._repo.revoke_remove_permission(guild_id, user_id)
        if not removed:
            raise PermissionNotGrantedError("permission not granted")

    def get_clan_register_channel(self, guild_id: int) -> int:
        channel_id = self._repo.get_clan_register_channel(guild_id)
        if channel_id is None:
            raise MissingClanRegisterChannelError("clan register channel missing")
        return channel_id

    def set_clan_register_channel(self, guild_id: int, channel_id: int) -> None:
        self._repo.set_clan_register_channel(guild_id, channel_id)

    def set_role_buy_price(self, guild_id: int, role_id: int, price: int) -> None:
        _require_positive_points(price)
        self._repo.set_role_buy_price(guild_id, role_id, price)

    def get_role_buy_price(self, guild_id: int, role_id: int) -> int | None:
        return self._repo.get_role_buy_price(guild_id, role_id)

    def validate_role_purchase(
        self, guild_id: int, role_id: int, user_id: int
    ) -> RolePurchase:
        price = self._repo.get_role_buy_price(guild_id, role_id)
        if price is None:
            raise RoleNotForSaleError("role is not for sale")
        points = self._repo.get_user_points(guild_id, user_id)
        if points is None or points < price:
            raise InsufficientPointsError("insufficient points")
        return RolePurchase(role_id=role_id, price=price)

    def charge_role_purchase(self, guild_id: int, user_id: int, price: int) -> None:
        self._repo.add_points(guild_id, user_id, -price)

    def refund_role_purchase(self, guild_id: int, user_id: int, price: int) -> None:
        self._repo.add_points(guild_id, user_id, price)


__all__ = [
    "InsufficientPointsError",
    "InvalidPointsError",
    "MissingClanRegisterChannelError",
    "OperationFailedError",
    "PermissionDeniedError",
    "PermissionNotGrantedError",
    "PointsService",
    "PointsServiceError",
    "RoleNotForSaleError",
    "RolePurchase",
    "TargetHasNoPointsError",
]
