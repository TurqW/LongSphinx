from discord import ApplicationContext, Bot, Interaction
from discord.utils import MISSING

from persistence import botconfig as conf


class LongSphinxContext(ApplicationContext):
    def __init__(self, bot: Bot, interaction: Interaction):
        super().__init__(bot, interaction)
        self.force_ephemeral = self._should_force_ephem()

    def _should_force_ephem(self):
        if not self.interaction.guild:
            return False
        if conf.get_object(self.interaction.guild, 'channelListBehavior') == 'allow':
            if self.interaction.channel.name in conf.get_object(self.interaction.guild, 'channels')\
                    or self.interaction.channel.id in conf.get_object(self.interaction.guild, 'channels'):
                return False
            return True
        if self.interaction.channel.name not in conf.get_object(self.interaction.guild, 'channels')\
                and self.interaction.channel.id not in conf.get_object(self.interaction.guild, 'channels'):
            return False
        return True

    async def respond(self, content, *args, ephemeral=False, embed=MISSING, **kwargs):
        if embed and not embed.colour:
            embed.color = conf.get_object(self.interaction.guild, 'embedColor')
        if self.force_ephemeral and not ephemeral:
            ephemeral = True
            content += '\n*This message is private because my slash commands are disabled in this channel.*'
        return await super().respond(content, *args, ephemeral=ephemeral, embed=embed, **kwargs)
