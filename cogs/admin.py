import re

from discord import Cog, Member
from discord.utils import find

from persistence import botconfig as conf
from discordclasses import utils

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
