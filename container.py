from __future__ import annotations

from client import BotClient, create_client
from database import PointsRepository, Database
from config import load_admin_ids, load_token
from dotenv import load_dotenv
from pathlib import Path
from utils import _parse_admin_ids
from dataclasses import dataclass
import discord
import os


@dataclass(frozen=True, slots=True)
class DBSettings:
    db_path: str
    timeout: float


@dataclass(frozen=True, slots=True)
class DiscordSettings:
    secret_token: str
    admin_ids: set[int]


@dataclass(frozen=True, slots=True)
class AppConfig:
    db_settings: DBSettings
    discord_settings: DiscordSettings


def __load_env_file(env_file: str | Path | None = None) -> None:
    if env_file is None:
        load_dotenv()
    else:
        path = Path(env_file)
        load_dotenv(dotenv_path=path)
    return


def load_discord_settings(
    raw_token: str | None = None, raw_admin_ids: str | None = None
) -> DiscordSettings:
    token = raw_token if raw_token is not None else load_token()
    if token is None or token.strip() == "":
        raise ValueError("Discord secret token is not provided.")
    secret_token = token.strip()

    if raw_admin_ids is None:
        admin_ids = load_admin_ids()
    else:
        if raw_admin_ids.strip() == "":
            raise ValueError("Discord admin IDs are not provided.")
        admin_ids = _parse_admin_ids(raw_admin_ids)

    return DiscordSettings(secret_token=secret_token, admin_ids=admin_ids)


def load_db_settings(
    raw_db_path: str | None = None, raw_timeout: str | None = None
) -> DBSettings:
    db_path = raw_db_path if raw_db_path is not None else os.getenv("DS_DB_PATH")
    db_path = db_path.strip() if db_path is not None else ""
    if db_path == "":
        db_path = "points.db"

    timeout_raw = raw_timeout if raw_timeout is not None else os.getenv("DS_DB_TIMEOUT")
    timeout_raw = timeout_raw.strip() if timeout_raw is not None else ""
    if timeout_raw == "":
        timeout = 5.0
    else:
        try:
            timeout = float(timeout_raw)
        except ValueError as exc:
            raise ValueError("DS_DB_TIMEOUT must be a float.") from exc
        if timeout <= 0:
            raise ValueError("DS_DB_TIMEOUT must be positive.")

    return DBSettings(db_path=db_path, timeout=timeout)


def load_config(env_file: str | Path | None = None) -> AppConfig:
    __load_env_file(env_file)
    discord_settings = load_discord_settings()
    db_settings = load_db_settings()
    return AppConfig(db_settings=db_settings, discord_settings=discord_settings)


def register_commands(
    client: BotClient, *, points_repo: PointsRepository, admin_ids: set[int]
) -> None:
    tree = client.tree

    @tree.command(name="point", description="あなたの現在のポイントを表示します")
    async def point_command(interaction: discord.Interaction) -> None:
        user_id = interaction.user.id
        points = points_repo.get_user_points(user_id)
        if points is None:
            await interaction.response.send_message("まだポイントがありません。")
            return
        embed = discord.Embed(
            title=f"{interaction.user.display_name}の",
            description=f"{points}ポイント",
            color=0x4EF47D,
        )
        await interaction.response.send_message(embed=embed)

    @tree.command(name="rank", description="ランキング上位10名を表示します。")
    async def rank_command(interaction: discord.Interaction) -> None:
        results = points_repo.get_top_rank(10)
        if not results:
            await interaction.response.send_message("まだランキングがありません。")
            return
        rank_embed = discord.Embed(title="**ポイントランキング**", color=0x4EF47D)
        for i, result in enumerate(results):
            user = await client.fetch_user(result["user_id"])
            if user is not None:
                rank_embed.add_field(
                    name=f"{i + 1}. {user.name}",
                    value=f"{result['points']}ポイント",
                    inline=False,
                )
            else:
                rank_embed.add_field(
                    name=f"{i + 1}. ユーザーが存在しません",
                    value=f"{result['points']}ポイント",
                    inline=False,
                )
        await interaction.response.send_message(embed=rank_embed)

    @tree.command(
        name="send", description="指定されたユーザーに指定された数のポイントを送信します。"
    )
    async def send_command(
        interaction: discord.Interaction, user: discord.Member, points: int
    ) -> None:
        if points <= 0:
            await interaction.response.send_message(
                "**ポイントは1以上で指定してください。**"
            )
            return
        sender_id = interaction.user.id
        recipient_id = user.id
        success = points_repo.send_points(sender_id, recipient_id, points)
        if not success:
            await interaction.response.send_message("**ポイントが足りません。**")
            return
        embed = discord.Embed(
            title="**ポイント送信！**",
            description=(
                f"**<@{sender_id}>が<@{recipient_id}>に{points}ポイント送信しました！**"
            ),
            color=discord.Color.green(),
        )
        await interaction.response.send_message(embed=embed)

    @tree.command(name="remove", description="ポイントを奪います")
    async def remove_command(
        interaction: discord.Interaction, user: discord.Member, points: int
    ) -> None:
        if points <= 0:
            await interaction.response.send_message(
                "**ポイントは1以上で指定してください。**"
            )
            return
        if interaction.user.id not in admin_ids:
            embed = discord.Embed(
                title="**エラー!**",
                description="**特定のユーザーのみ使用できます。**",
                color=0xFF0000,
            )
            await interaction.response.send_message(embed=embed)
            return
        sender_id = interaction.user.id
        recipient_id = user.id
        recipient_points = points_repo.get_user_points(recipient_id)
        if recipient_points is None:
            embed = discord.Embed(
                title="**エラー!**",
                description=f"**{user.display_name}さんはまだポイントを持っていません！**",
                color=0xFF0000,
            )
            await interaction.response.send_message(embed=embed)
            return
        if recipient_points < points:
            embed = discord.Embed(
                title="**エラー!**",
                description=f"**{user.display_name}さんは{points}ポイント持っていません！**",
                color=0xFF0000,
            )
            await interaction.response.send_message(embed=embed)
            return
        success = points_repo.remove_points(sender_id, recipient_id, points)
        if not success:
            embed = discord.Embed(
                title="**エラー!**",
                description="**ポイントの移動に失敗しました。**",
                color=0xFF0000,
            )
            await interaction.response.send_message(embed=embed)
            return
        embed = discord.Embed(
            title="**ポイント剥奪！**",
            description=(
                f"**{user.display_name}さんから{points}ポイント奪いました！"
                f"<@{sender_id}>さんに{points}ポイント与えました！**"
            ),
            color=discord.Color.red(),
        )
        await interaction.response.send_message(embed=embed)


def create_bot_client(config: AppConfig) -> BotClient:
    db_path = Path(config.db_settings.db_path)
    if db_path.parent != Path("."):
        db_path.parent.mkdir(parents=True, exist_ok=True)
    db = Database(db_path=str(db_path), timeout=config.db_settings.timeout)
    points_repo = PointsRepository(db)
    points_repo.ensure_schema()
    client = create_client(points_repo=points_repo)
    register_commands(
        client, points_repo=points_repo, admin_ids=config.discord_settings.admin_ids
    )
    return client
