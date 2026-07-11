"""Discord bot that creates welcome cards from member roles."""

from typing import Optional

import discord


COMMAND = "!welcome"
WELCOME_CHANNEL = "welcome"
MESSAGE_TIMEOUT = 10


def readable_list(items: list[str]) -> str:
    """Join a list using natural-language punctuation."""
    if len(items) == 1:
        return items[0]

    if len(items) == 2:
        return f"{items[0]} and {items[1]}"

    return f'{", ".join(items[:-1])}, and {items[-1]}'


def category_statement(category: str, values: list[str]) -> str:
    """Turn a role category and its values into a profile sentence."""
    joined_values = readable_list(values)

    statements = {
        "research interest": f"I am interested in {joined_values}.",
        "programming language": f"I program in {joined_values}.",
        "background": f"My background is in {joined_values}.",
        "education": f"My education level is {joined_values}.",
        "trading style": (
            f"My trading interests / styles include {joined_values}."
        ),
        "infrastructure": f"I use {joined_values}.",
        "operating system": f"I use {joined_values}.",
        "region": f"I am based in {joined_values}.",
        "age": f"My age group is {joined_values}.",
        "asset": f"I am interested in {joined_values}.",
    }

    if category == "career goal":
        if len(values) == 1:
            return f"I am an aspiring {joined_values}."

        return f"I aspire to work in {joined_values}."

    return statements.get(
        category,
        f"My {category} is {joined_values}.",
    )


def classify_roles(
    member: discord.Member,
) -> tuple[dict[str, list[str]], list[str]]:
    """Group `Category:Value` roles and retain unstructured role names."""
    categories: dict[str, list[str]] = {}
    other_roles: list[str] = []

    # Reverse Discord's role order so cards read highest to lowest.
    for role in reversed(member.roles):
        if role.is_default():
            continue

        if ":" not in role.name:
            other_roles.append(role.name)
            continue

        raw_category, raw_value = role.name.split(":", 1)

        category = (
            raw_category
            .replace("_", " ")
            .strip()
            .lower()
        )

        value = (
            raw_value
            .replace("_", " ")
            .strip()
        )

        if category and value:
            categories.setdefault(category, []).append(value)
        else:
            other_roles.append(role.name)

    return categories, other_roles


def build_id_card(member: discord.Member) -> discord.Embed:
    """Build a Discord embed containing the member's role profile."""
    categories, other_roles = classify_roles(member)

    color = (
        member.color
        if member.color.value
        else discord.Color.blurple()
    )

    embed = discord.Embed(
        title="Welcome — Member ID Card",
        description=f"Hi. I am {member.mention}",
        color=color,
    )

    embed.set_thumbnail(url=member.display_avatar.url)

    for category, values in categories.items():
        embed.add_field(
            name=category.title(),
            value=category_statement(category, values)[:1024],
            inline=False,
        )

    if other_roles:
        embed.add_field(
            name="Other Roles",
            value=", ".join(other_roles)[:1024],
            inline=False,
        )
    elif not categories:
        embed.add_field(
            name="Roles",
            value="No roles",
            inline=False,
        )

    embed.set_footer(text=f"User ID: {member.id}")

    return embed


def find_welcome_channel(
    guild: discord.Guild,
) -> Optional[discord.TextChannel]:
    """Find a #welcome channel where the bot can send embeds."""
    channel = discord.utils.find(
        lambda item: item.name.lower() == WELCOME_CHANNEL,
        guild.text_channels,
    )

    if channel is None or guild.me is None:
        return None

    permissions = channel.permissions_for(guild.me)

    if permissions.send_messages and permissions.embed_links:
        return channel

    return None


class WelcomerClient(discord.Client):
    """Handle the administrator-only welcome-card command."""

    async def on_ready(self) -> None:
        print(f"[Welcomer] Logged in as {self.user}")
        print(
            f"[Welcomer] Admins can use "
            f"{COMMAND} @member."
        )

    async def on_message(
        self,
        message: discord.Message,
    ) -> None:
        if message.author.bot or message.guild is None:
            return

        command, _, _ = message.content.partition(" ")

        if command.lower() != COMMAND:
            return

        if not message.author.guild_permissions.administrator:
            await message.channel.send(
                f"Only administrators can use `{COMMAND}`.",
                delete_after=MESSAGE_TIMEOUT,
            )
            return

        if not message.mentions:
            await message.channel.send(
                f"Mention a member, for example: "
                f"`{COMMAND} @someone`",
                delete_after=MESSAGE_TIMEOUT,
            )
            return

        channel = find_welcome_channel(message.guild)

        if channel is None:
            await message.channel.send(
                f"I cannot find `#{WELCOME_CHANNEL}`, "
                "or I cannot send embeds there.",
                delete_after=MESSAGE_TIMEOUT,
            )
            return

        member = message.mentions[0]

        try:
            member = await message.guild.fetch_member(member.id)
        except discord.HTTPException:
            # The member object from the mention remains usable.
            pass

        await channel.send(embed=build_id_card(member))

        try:
            await message.delete()
        except discord.Forbidden:
            print(
                "[Welcomer] Could not delete the command: "
                "Manage Messages is required."
            )

        await message.channel.send(
            f"Permanent welcome ID created for "
            f"{member.mention} in {channel.mention}.",
            delete_after=MESSAGE_TIMEOUT,
        )


def create_bot() -> WelcomerClient:
    """Create and configure the Welcomer Discord client."""
    intents = discord.Intents.default()
    intents.members = True
    intents.message_content = True

    return WelcomerClient(intents=intents)
    