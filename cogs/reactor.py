import re
from datetime import datetime, timedelta

from discord import Cog
from discord.enums import MessageType

from persistence import botconfig as conf

recent = {}


class Reactor(Cog):
    def __init__(self, bot):
        self.bot = bot

    @Cog.listener('on_message')
    async def on_message(self, message):
        if message.type != MessageType.default and message.type != MessageType.reply:
            return
        reacts = conf.get_object(message.guild, 'autoreact')
        if reacts:
            for emoji in reacts:
                for trigger in emoji['triggers']:
                    if re.search(trigger, message.content, re.IGNORECASE) and timecheck(
                            emoji['emoji'] + str(message.channel.id)):
                        recent[emoji['emoji'] + str(message.channel.id)] = datetime.now()
                        await message.add_reaction(emoji['emoji'])
        replies = conf.get_object(message.guild, 'autoreply')
        if replies:
            for reply in replies:
                for trigger in reply['triggers']:
                    if re.search(trigger, message.content, re.IGNORECASE) and timecheck(
                            reply['text'] + str(message.channel.id)):
                        recent[reply['text'] + str(message.channel.id)] = datetime.now()
                        await message.channel.send(content=reply['text'], reference=message)


def timecheck(key):
    try:
        return recent[key] < datetime.now() - timedelta(minutes=5)
    except KeyError:
        return True
