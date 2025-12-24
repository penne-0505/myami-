import discord
from discord.ext import commands
import os
import sqlite3
from discord import app_commands


TOKEN = os.getenv("DS_SECRET_TOKEN")


intents = discord.Intents.default()
client = discord.Client(intents=intents)
tree = app_commands.CommandTree(client)


@client.event
async def on_ready():
    print("起動完了")
    await tree.sync()  # スラッシュコマンドを同期


# SQLiteのデータベースに接続する
conn = sqlite3.connect("points.db")
c = conn.cursor()

# ポイントを保存するテーブルを作成する
c.execute(
    "CREATE TABLE IF NOT EXISTS points (user_id INTEGER PRIMARY KEY, points INTEGER)"
)


@client.event
async def on_message(message):
    if message.author.bot:
        return

    # ポイントを加算する処理
    user_id = message.author.id
    c.execute(
        "INSERT OR IGNORE INTO points (user_id, points) VALUES (?, ?)", (user_id, 0)
    )
    c.execute("UPDATE points SET points = points + 1 WHERE user_id = ?", (user_id,))
    conn.commit()


# ポイントがいくつか表示する
@tree.command(name="point", description="あなたの現在のポイントを表示します")
async def point_command(interaction: discord.Interaction):
    user_id = interaction.user.id

    c.execute("SELECT points FROM points WHERE user_id = ?", (user_id,))
    result = c.fetchone()
    if result is not None:
        embed = discord.Embed(
            title=f"{interaction.user.display_name}の",
            description=f"{result[0]}ポイント",
            color=0x4EF47D,
        )
        await interaction.response.send_message(embed=embed)


@tree.command(name="rank", description="ランキング上位10名を表示します。")
async def rank_command(interaction: discord.Interaction):
    c.execute("SELECT user_id, points FROM points ORDER BY points DESC LIMIT 10")
    results = c.fetchall()
    if results:
        rank_embed = discord.Embed(title="**ポイントランキング**", color=0x4EF47D)
        for i, result in enumerate(results):
            user = await client.fetch_user(result[0])
            if user is not None:
                rank_embed.add_field(
                    name=f"{i + 1}. {user.name}",
                    value=f"{result[1]}ポイント",
                    inline=False,
                )
            else:
                rank_embed.add_field(
                    name=f"{i + 1}. ユーザーが存在しません",
                    value=f"{result[1]}ポイント",
                    inline=False,
                )
        await interaction.response.send_message(embed=rank_embed)


@tree.command(
    name="send", description="指定されたユーザーに指定された数のポイントを送信します。"
)
async def send_command(
    interaction: discord.Interaction, user: discord.Member, points: int
):
    if points <= 0:
        await interaction.response.send_message(
            "**ポイントは1以上で指定してください。**"
        )
        return

    sender_id = interaction.user.id
    recipient_id = user.id
    recipient = await client.fetch_user(recipient_id)

    # 送信者のポイントを減らす
    c.execute(
        "INSERT OR IGNORE INTO points (user_id, points) VALUES (?, ?)", (sender_id, 0)
    )
    conn.commit()
    c.execute("SELECT points FROM points WHERE user_id = ?", (sender_id,))
    conn.commit()
    sender_points = c.fetchone()[0]
    if sender_points < points:
        await interaction.response.send_message("**ポイントが足りません。**")
        return
    c.execute(
        "UPDATE points SET points = points - ? WHERE user_id = ?", (points, sender_id)
    )
    conn.commit()

    # 受信者のポイントを増やす
    c.execute(
        "INSERT OR IGNORE INTO points (user_id, points) VALUES (?, ?)",
        (recipient_id, 0),
    )
    conn.commit()
    c.execute(
        "UPDATE points SET points = points + ? WHERE user_id = ?",
        (points, recipient_id),
    )
    conn.commit()

    embed = discord.Embed(
        title=f"**ポイント送信！**",
        description=f"**<@{sender_id}>が<@{recipient_id}>に{points}ポイント送信しました！**",
        color=discord.Color.green(),
    )
    await interaction.response.send_message(embed=embed)


@tree.command(name="remove", description="ポイントを奪います")
async def send_command(
    interaction: discord.Interaction, user: discord.Member, points: int
):
    if interaction.user.id not in [
        711421164194365471,
        720241890662023268,
        907286924354551829,
    ]:
        embed = discord.Embed(
            title="**エラー!**",
            description="**特定のユーザーのみ使用できます。**",
            color=0xFF0000,
        )
        await interaction.response.send_message(embed=embed)
        return

    c.execute("SELECT points FROM points WHERE user_id = ?", (user.id,))
    result = c.fetchone()

    sender_id = interaction.user.id
    recipient_id = user.id
    recipient = await client.fetch_user(recipient_id)

    if result is None:
        embed = discord.Embed(
            title="**エラー!**",
            description=f"**{user.display_name}さんはまだポイントを持っていません！**",
            color=0xFF0000,
        )
        await interaction.response.send_message(embed=embed)
        return

    if result[0] < points:
        embed = discord.Embed(
            title="**エラー!**",
            description=f"**{user.display_name}さんは{points}ポイント持っていません！**",
            color=0xFF0000,
        )
        await interaction.response.send_message(embed=embed)
        return

    # 受信者のポイントを減らす
    c.execute(
        "UPDATE points SET points = points - ? WHERE user_id = ?",
        (points, recipient_id),
    )
    conn.commit()

    # コマンド実行者のポイントを増やす
    c.execute(
        "INSERT OR IGNORE INTO points (user_id, points) VALUES (?, ?)", (sender_id, 0)
    )
    conn.commit()
    c.execute(
        "UPDATE points SET points = points + ? WHERE user_id = ?", (points, sender_id)
    )
    conn.commit()

    embed = discord.Embed(
        title="**ポイント剥奪！**",
        description=f"**{user.display_name}さんから{points}ポイント奪いました！<@{sender_id}>さんに{points}ポイント与えました！**",
        color=discord.Color.red(),
    )
    await interaction.response.send_message(embed=embed)


client.run(TOKEN)
