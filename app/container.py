from __future__ import annotations

from bot.client import BotClient, create_client
from service.database import Database
from app.config import load_token
from dotenv import load_dotenv
from dataclasses import dataclass
from pathlib import Path
import discord
import os

from service.repository import PointsRepository


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


def __load_env_file(env_file: str | Path | None = None) -> None:
    if env_file is None:
        load_dotenv()
    else:
        path = Path(env_file)
        load_dotenv(dotenv_path=path)
    return


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

    return DBSettings(supabase_url=supabase_url, service_role_key=service_role_key)


def load_config(env_file: str | Path | None = None) -> AppConfig:
    __load_env_file(env_file)
    discord_settings = load_discord_settings()
    db_settings = load_db_settings()
    return AppConfig(db_settings=db_settings, discord_settings=discord_settings)


def register_commands(client: BotClient, *, points_repo: PointsRepository) -> None:
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
        name="send",
        description="指定されたユーザーに指定された数のポイントを送信します。",
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
        if not _has_remove_permission(interaction, points_repo):
            await interaction.response.send_message(
                embed=_permission_error_embed("ポイント剥奪権限がありません。")
            )
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

    @tree.command(
        name="permit-remove",
        description="ポイント剥奪を許可/解除します（サーバー管理者のみ）",
    )
    async def permit_remove_command(
        interaction: discord.Interaction, user: discord.Member, allowed: bool
    ) -> None:
        if not _is_guild_admin(interaction):
            await interaction.response.send_message(
                embed=_permission_error_embed("サーバー管理者のみ実行できます。")
            )
            return
        target_id = user.id
        if allowed:
            points_repo.grant_remove_permission(target_id)
            embed = discord.Embed(
                title="**ポイント剥奪権限を付与しました**",
                description=f"**{user.display_name}さんに権限を付与しました。**",
                color=discord.Color.green(),
            )
            await interaction.response.send_message(embed=embed)
            return
        removed = points_repo.revoke_remove_permission(target_id)
        if not removed:
            embed = discord.Embed(
                title="**エラー!**",
                description="**対象ユーザーは権限を持っていません。**",
                color=0xFF0000,
            )
            await interaction.response.send_message(embed=embed)
            return
        embed = discord.Embed(
            title="**ポイント剥奪権限を解除しました**",
            description=f"**{user.display_name}さんの権限を解除しました。**",
            color=discord.Color.red(),
        )
        await interaction.response.send_message(embed=embed)

    @tree.command(
        name="clan-register",
        description="クラン登録を申請します。",
    )
    async def clan_register_command(
        interaction: discord.Interaction, clan_name: str
    ) -> None:
        if interaction.guild is None:
            await interaction.response.send_message(
                embed=_permission_error_embed("サーバー内で使用してください。")
            )
            return
        channel_id = points_repo.get_clan_register_channel(interaction.guild.id)
        if channel_id is None:
            await interaction.response.send_message(
                embed=_permission_error_embed("通知先チャンネルが未設定です。")
            )
            return
        channel = await _fetch_text_channel(
            client, guild=interaction.guild, channel_id=channel_id
        )
        if channel is None:
            await interaction.response.send_message(
                embed=_permission_error_embed("通知先チャンネルが見つかりません。")
            )
            return
        embed = discord.Embed(
            title="**クラン登録申請**",
            color=discord.Color.blurple(),
        )
        embed.add_field(name="クラン名", value=clan_name, inline=False)
        embed.add_field(name="代表者", value=interaction.user.mention, inline=False)
        embed.add_field(name="サーバー", value=interaction.guild.name, inline=False)
        await channel.send(embed=embed)
        await interaction.response.send_message("申請を送信しました。")

    @tree.command(
        name="clan-register-channel",
        description="クラン登録申請の通知先チャンネルを設定します（サーバー管理者のみ）",
    )
    async def clan_register_channel_command(
        interaction: discord.Interaction, channel: discord.TextChannel
    ) -> None:
        if not _is_guild_admin(interaction):
            await interaction.response.send_message(
                embed=_permission_error_embed("サーバー管理者のみ実行できます。")
            )
            return
        if interaction.guild is None:
            await interaction.response.send_message(
                embed=_permission_error_embed("サーバー内で使用してください。")
            )
            return
        if channel.guild.id != interaction.guild.id:
            await interaction.response.send_message(
                embed=_permission_error_embed(
                    "同じサーバーのチャンネルを指定してください。"
                )
            )
            return
        points_repo.set_clan_register_channel(interaction.guild.id, channel.id)
        embed = discord.Embed(
            title="**クラン登録通知チャンネルを設定しました**",
            description=f"**通知先: {channel.mention}**",
            color=discord.Color.green(),
        )
        await interaction.response.send_message(embed=embed)

    @tree.command(
        name="role-buy-register",
        description="購入可能ロールと価格を登録します（サーバー管理者のみ）",
    )
    async def role_buy_register_command(
        interaction: discord.Interaction, role: discord.Role, price: int
    ) -> None:
        if not _is_guild_admin(interaction):
            await interaction.response.send_message(
                embed=_permission_error_embed("サーバー管理者のみ実行できます。")
            )
            return
        if interaction.guild is None:
            await interaction.response.send_message(
                embed=_permission_error_embed("サーバー内で使用してください。")
            )
            return
        if role.guild.id != interaction.guild.id:
            await interaction.response.send_message(
                embed=_permission_error_embed(
                    "同じサーバーのロールを指定してください。"
                )
            )
            return
        if price <= 0:
            await interaction.response.send_message(
                embed=_permission_error_embed("価格は1以上で指定してください。")
            )
            return
        points_repo.set_role_buy_price(interaction.guild.id, role.id, price)
        embed = discord.Embed(
            title="**ロール購入を登録しました**",
            description=f"**対象: {role.mention} / 価格: {price}ポイント**",
            color=discord.Color.green(),
        )
        await interaction.response.send_message(embed=embed)

    @tree.command(name="role-buy", description="ロールを購入します。")
    async def role_buy_command(
        interaction: discord.Interaction, role: discord.Role
    ) -> None:
        if interaction.guild is None:
            await interaction.response.send_message(
                embed=_permission_error_embed("サーバー内で使用してください。")
            )
            return
        member = interaction.user
        if not isinstance(member, discord.Member):
            await interaction.response.send_message(
                embed=_permission_error_embed("サーバー内で使用してください。")
            )
            return
        if role.guild.id != interaction.guild.id:
            await interaction.response.send_message(
                embed=_permission_error_embed(
                    "同じサーバーのロールを指定してください。"
                )
            )
            return
        if role in member.roles:
            embed = discord.Embed(
                title="**購入済み**",
                description="**既にロールを所持しています。**",
                color=discord.Color.blue(),
            )
            await interaction.response.send_message(embed=embed)
            return
        price = points_repo.get_role_buy_price(interaction.guild.id, role.id)
        if price is None:
            await interaction.response.send_message(
                embed=_permission_error_embed("このロールは購入対象ではありません。")
            )
            return
        points = points_repo.get_user_points(member.id)
        if points is None or points < price:
            await interaction.response.send_message(
                embed=_permission_error_embed("ポイントが足りません。")
            )
            return
        points_repo.add_points(member.id, -price)
        try:
            await member.add_roles(role, reason="role buy")
        except discord.Forbidden:
            points_repo.add_points(member.id, price)
            await interaction.response.send_message(
                embed=_permission_error_embed("ロールを付与できませんでした。")
            )
            return
        except discord.HTTPException:
            points_repo.add_points(member.id, price)
            await interaction.response.send_message(
                embed=_permission_error_embed("ロール付与に失敗しました。")
            )
            return
        embed = discord.Embed(
            title="**購入完了**",
            description=f"**{role.mention} を付与しました。**",
            color=discord.Color.green(),
        )
        await interaction.response.send_message(embed=embed)


def create_bot_client(config: AppConfig) -> BotClient:
    db = Database(
        url=config.db_settings.supabase_url,
        service_role_key=config.db_settings.service_role_key,
    )
    points_repo = PointsRepository(db)
    points_repo.ensure_schema()
    client = create_client(points_repo=points_repo)
    register_commands(client, points_repo=points_repo)
    return client


def _is_guild_admin(interaction: discord.Interaction) -> bool:
    if interaction.guild is None:
        return False
    user = interaction.user
    if not isinstance(user, discord.Member):
        return False
    perms = user.guild_permissions
    return perms.administrator or perms.manage_guild


def _has_remove_permission(
    interaction: discord.Interaction, points_repo: PointsRepository
) -> bool:
    if _is_guild_admin(interaction):
        return True
    return points_repo.has_remove_permission(interaction.user.id)


def _permission_error_embed(message: str) -> discord.Embed:
    return discord.Embed(
        title="**エラー!**",
        description=f"**{message}**",
        color=0xFF0000,
    )


async def _fetch_text_channel(
    client: BotClient, *, guild: discord.Guild, channel_id: int
) -> discord.TextChannel | None:
    channel = guild.get_channel(channel_id)
    if isinstance(channel, discord.TextChannel):
        return channel
    try:
        fetched = await client.fetch_channel(channel_id)
    except discord.NotFound:
        return None
    except discord.HTTPException:
        return None
    if isinstance(fetched, discord.TextChannel) and fetched.guild.id == guild.id:
        return fetched
    return None
