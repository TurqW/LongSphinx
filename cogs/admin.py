import re
import asyncio
from datetime import datetime, timezone

from discord import Cog, Member, slash_command, Option, Interaction, ChannelType
from discord.utils import find

from persistence import botconfig as conf
from discordclasses import utils
from discordclasses.confirm import Confirm

# Should this be persisted?
noobs = []


async def first_message_link(message):
    automod = conf.get_object(message.guild, 'automod')
    if automod['firstMessage'] and (message.guild.id, message.author.id) in noobs:
        if re.search('http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\(\), ]|(?:%[0-9a-fA-F][0-9a-fA-F]))+',
                     message.content):
            await dungeon(
                ', your first message on the server was auto-flagged as potential spam. A mod will be here shortly to '
                'review your case. Your message: ```\n',
                message)
        noobs.remove((message.guild.id, message.author.id))


async def no_role_link(message):
    automod = conf.get_object(message.guild, 'automod')
    if 'noRole' in automod and automod['noRole'] and len(message.author.roles) <= 1:
        for blocked in automod['noRole']:
            if blocked in message.content:
                await dungeon(
                    ', your message has been auto-flagged as potential spam. A mod will be here shortly to review '
                    'your case. Your message: ```\n',
                    message)


async def dungeon(text, message):
    automod = conf.get_object(message.guild, 'automod')
    role = find(lambda r: r.name.lower() == automod['role'].lower(), message.guild.roles)
    dungeon_channel = utils.find_channel(automod['channel'], message.guild)
    await message.author.add_roles(role)
    await dungeon_channel.send(message.author.mention + text + message.content.replace('`', '') + '\n```')
    try:
        await message.delete()
        return True
    except Exception as e:
        print(e)


def delete_history(messages):
    async def delete_history_callback(interaction: Interaction):
        await interaction.response.edit_message(content="Working...", view=None)
        await asyncio.gather(*[message.delete() for message in messages])

    return delete_history_callback


class AdminHelper(Cog):
    def __init__(self, bot):
        self.bot = bot

    @Cog.listener()
    async def on_member_join(self, member: Member):
        noobs.append((member.guild.id, member.id))

    @Cog.listener()
    async def on_message(self, message):
        await first_message_link(message)
        await no_role_link(message)

    #@slash_command(name='gdpr', description='A right to be forgotten')#,
                   #guild_ids=[494373430637101058])
    async def gdpr(self, ctx,
                       server: Option(str, 'Guild ID'),
                       user: Option(str, 'User ID')
                       ):
        try:
            guild = await self.bot.fetch_guild(server)
        except:
            await ctx.respond("Guild not found.", ephemeral=True)
            return
        messages = []
        earliest = datetime.now(timezone.utc)
        foundOne = True
        await ctx.defer()
        while foundOne:
            foundOne = False
            for channel in await guild.fetch_channels():
                if channel.type == ChannelType.text:
                    try:
                        async for message in channel.history(before=earliest):
                            if str(message.author.id) == user:
                                foundOne = True
                                messages.append(message)
                            if message.created_at < earliest:
                                earliest = message.created_at
                    except Exception as e:
                        print(e)
        msg = f'Found {len(messages)} messages. Delete all (deletion may find more)?'
        confirm_view = Confirm(delete_history(messages))
        await ctx.respond(msg, ephemeral=True, view=confirm_view)
