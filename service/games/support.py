from __future__ import annotations

import math

from bot.constants import (
    CANCEL_WORDS,
    COIN_ALIASES,
    COIN_LABELS,
    JANKEN_ALIASES,
    JANKEN_LABELS,
)

MIN_BET = 100


def normalize_digits(raw: str) -> str:
    return raw.translate(
        str.maketrans(
            "０１２３４５６７８９",
            "0123456789",
        )
    )


def parse_bet(args: list[str]) -> int | None:
    if not args:
        return None
    for arg in args:
        normalized = normalize_digits(arg)
        if normalized.isdigit():
            return int(normalized)
    return None


def parse_bet_with_choice(
    args: list[str], parser
) -> tuple[int | None, str | None]:
    bet = None
    choice = None
    for arg in args:
        normalized = normalize_digits(arg)
        if bet is None and normalized.isdigit():
            bet = int(normalized)
            continue
        if choice is None:
            parsed = parser(normalized)
            if parsed is not None:
                choice = parsed
    return bet, choice


def validate_bet(bet: int) -> str | None:
    if bet <= 0:
        return "賭けるポイントは1以上で指定してください。"
    if bet < MIN_BET:
        return f"賭けるポイントは {MIN_BET} 以上で指定してください。"
    return None


def ensure_balance(
    points_repo,
    guild_id: int,
    user_id: int,
    bet: int,
    *,
    max_loss_multiplier: float,
) -> tuple[bool, int, int]:
    points = points_repo.get_user_points(guild_id, user_id) or 0
    required = int(math.ceil(bet * max_loss_multiplier))
    return points >= required, required, points


def apply_payout(
    points_repo, guild_id: int, user_id: int, bet: int, multiplier: float
) -> int:
    payout = int(round(bet * multiplier))
    if payout != 0:
        points_repo.add_points(guild_id, user_id, payout)
    return payout


def is_cancel_message(raw: str) -> bool:
    normalized = raw.strip().lower()
    return normalized in {word.lower() for word in CANCEL_WORDS}


def cancel_words_label() -> str:
    return "/".join(CANCEL_WORDS)


def parse_janken_choice(raw: str) -> str | None:
    normalized = raw.strip().lower()
    for key, aliases in JANKEN_ALIASES.items():
        if normalized in {alias.lower() for alias in aliases}:
            return key
    return None


def parse_coin_choice(raw: str) -> str | None:
    normalized = raw.strip().lower()
    for key, aliases in COIN_ALIASES.items():
        if normalized in {alias.lower() for alias in aliases}:
            return key
    return None


def janken_result(player: str, opponent: str) -> str:
    if player == opponent:
        return "draw"
    wins = {
        ("rock", "scissors"),
        ("scissors", "paper"),
        ("paper", "rock"),
    }
    return "win" if (player, opponent) in wins else "lose"


def janken_label(choice: str) -> str:
    return JANKEN_LABELS.get(choice, choice)


def coin_label(choice: str) -> str:
    return COIN_LABELS.get(choice, choice)


__all__ = [
    "MIN_BET",
    "normalize_digits",
    "parse_bet",
    "parse_bet_with_choice",
    "validate_bet",
    "ensure_balance",
    "apply_payout",
    "is_cancel_message",
    "cancel_words_label",
    "parse_janken_choice",
    "parse_coin_choice",
    "janken_result",
    "janken_label",
    "coin_label",
]
