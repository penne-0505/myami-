from __future__ import annotations

import discord

from bot.client import BotClient
from service.points_service import (
    InsufficientPointsError,
    InvalidPointsError,
    MissingClanRegisterChannelError,
    PermissionDeniedError,
    PermissionNotGrantedError,
    PointsService,
    PointsServiceError,
    RoleNotForSaleError,
    TargetHasNoPointsError,
)


def register_commands(client: BotClient, *, points_service: PointsService) -> None:
    tree = client.tree

    @tree.command(name="point", description="あなたの現在のポイントを表示します")
    async def point_command(interaction: discord.Interaction) -> None:
        if interaction.guild is None:
            await interaction.response.send_message(
                embed=_permission_error_embed("サーバー内で使用してください。")
            )
            return
        user_id = interaction.user.id
        points = points_service.get_user_points(interaction.guild.id, user_id)
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
        if interaction.guild is None:
            await interaction.response.send_message(
                embed=_permission_error_embed("サーバー内で使用してください。")
            )
            return
        results = points_service.get_top_rank(interaction.guild.id, 10)
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
        if interaction.guild is None:
            await interaction.response.send_message(
                embed=_permission_error_embed("サーバー内で使用してください。")
            )
            return
        if points <= 0:
            await interaction.response.send_message(
                "**ポイントは1以上で指定してください。**"
            )
            return
        sender_id = interaction.user.id
        recipient_id = user.id
        try:
            points_service.send_points(
                interaction.guild.id, sender_id, recipient_id, points
            )
        except InsufficientPointsError:
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
        if interaction.guild is None:
            await interaction.response.send_message(
                embed=_permission_error_embed("サーバー内で使用してください。")
            )
            return
        if points <= 0:
            await interaction.response.send_message(
                "**ポイントは1以上で指定してください。**"
            )
            return
        sender_id = interaction.user.id
        recipient_id = user.id
        try:
            points_service.remove_points(
                interaction.guild.id,
                sender_id,
                recipient_id,
                points,
                is_admin=_is_guild_admin(interaction),
            )
        except PermissionDeniedError:
            await interaction.response.send_message(
                embed=_permission_error_embed("ポイント剥奪権限がありません。")
            )
            return
        except TargetHasNoPointsError:
            embed = discord.Embed(
                title="**エラー!**",
                description=f"**{user.display_name}さんはまだポイントを持っていません！**",
                color=0xFF0000,
            )
            await interaction.response.send_message(embed=embed)
            return
        except InsufficientPointsError:
            embed = discord.Embed(
                title="**エラー!**",
                description=f"**{user.display_name}さんは{points}ポイント持っていません！**",
                color=0xFF0000,
            )
            await interaction.response.send_message(embed=embed)
            return
        except PointsServiceError:
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
        if interaction.guild is None:
            await interaction.response.send_message(
                embed=_permission_error_embed("サーバー内で使用してください。")
            )
            return
        target_id = user.id
        if allowed:
            points_service.grant_remove_permission(interaction.guild.id, target_id)
            embed = discord.Embed(
                title="**ポイント剥奪権限を付与しました**",
                description=f"**{user.display_name}さんに権限を付与しました。**",
                color=discord.Color.green(),
            )
            await interaction.response.send_message(embed=embed)
            return
        try:
            points_service.revoke_remove_permission(interaction.guild.id, target_id)
        except PermissionNotGrantedError:
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
        try:
            channel_id = points_service.get_clan_register_channel(interaction.guild.id)
        except MissingClanRegisterChannelError:
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
        points_service.set_clan_register_channel(interaction.guild.id, channel.id)
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
        try:
            points_service.set_role_buy_price(interaction.guild.id, role.id, price)
        except InvalidPointsError:
            await interaction.response.send_message(
                embed=_permission_error_embed("価格は1以上で指定してください。")
            )
            return
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
        try:
            purchase = points_service.validate_role_purchase(
                interaction.guild.id, role.id, member.id
            )
        except RoleNotForSaleError:
            await interaction.response.send_message(
                embed=_permission_error_embed("このロールは購入対象ではありません。")
            )
            return
        except InsufficientPointsError:
            await interaction.response.send_message(
                embed=_permission_error_embed("ポイントが足りません。")
            )
            return
        points_service.charge_role_purchase(
            interaction.guild.id, member.id, purchase.price
        )
        try:
            await member.add_roles(role, reason="role buy")
        except discord.Forbidden:
            points_service.refund_role_purchase(
                interaction.guild.id, member.id, purchase.price
            )
            await interaction.response.send_message(
                embed=_permission_error_embed("ロールを付与できませんでした。")
            )
            return
        except discord.HTTPException:
            points_service.refund_role_purchase(
                interaction.guild.id, member.id, purchase.price
            )
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


def _is_guild_admin(interaction: discord.Interaction) -> bool:
    if interaction.guild is None:
        return False
    user = interaction.user
    if not isinstance(user, discord.Member):
        return False
    perms = user.guild_permissions
    return perms.administrator or perms.manage_guild


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


__all__ = ["register_commands"]
