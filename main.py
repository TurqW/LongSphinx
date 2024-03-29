import logging
import sys
from asyncio import new_event_loop

from discord import Intents, Bot

from persistence import botconfig as conf
from discordclasses import utils
from cogs.colors import ColorCommands
from cogs.dice import RollCommands
from cogs.misc import MiscCommands
from cogs.notice import Notices
from cogs.pet import PetCommands
from cogs.reactor import Reactor
from cogs.reminder import Reminders
from cogs.rep import RepCommands
from cogs.role_manager import RoleManager
from cogs.userconfig import ConfigManager
from cogs.admin import AdminHelper
from cogs.writesprint import WriteSprint
from cogs.rss import Feeds
from discordclasses.context import LongSphinxContext

utils.check_path('logs')

bot_name = 'None'
if len(sys.argv) > 1:
    bot_name = sys.argv[1]
else:
    print('Usage: python longsphinx.py <bot name>')
    exit(-1)

conf.__init__('config.yaml', bot_name)

logging.basicConfig(
    filename=f'logs/{bot_name}.log',
    format='%(asctime)s %(levelname)-8s %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S',
    level=logging.DEBUG)
logging.getLogger('discord').setLevel(logging.WARNING)
logging.getLogger('websockets').setLevel(logging.WARNING)
log = logging.getLogger('LongSphinx')

token_file_name = f'{bot_name}.token'

with open(token_file_name, 'r') as token_file:
    TOKEN = token_file.readline().strip()

is_reminder_set = False

intents = Intents.default()
# PyCharm thinks these fields don't exist and also that they're read-only. Both are false.
# noinspection PyDunderSlots,PyUnresolvedReferences
intents.members = True
# noinspection PyDunderSlots,PyUnresolvedReferences
intents.message_content = True


class LongSphinx(Bot):
    async def get_application_context(self, interaction, cls=LongSphinxContext):
        # This override lets us change the behavior of ctx.respond
        return await super().get_application_context(interaction, cls=cls)


if bot_name == 'dev':
    bot = LongSphinx(intents=intents, loop=new_event_loop(), debug_guilds=[489197880809095168])
else:
    bot = LongSphinx(intents=intents, loop=new_event_loop())

bot.add_cog(ColorCommands(bot))
bot.add_cog(ConfigManager(bot))
bot.add_cog(MiscCommands(bot))
bot.add_cog(Notices(bot))
bot.add_cog(PetCommands(bot))
bot.add_cog(Reactor(bot))
bot.add_cog(Reminders(bot))
bot.add_cog(RepCommands(bot))
bot.add_cog(RoleManager(bot))
bot.add_cog(RollCommands(bot))
bot.add_cog(AdminHelper(bot))
bot.add_cog(WriteSprint(bot))
bot.add_cog(Feeds(bot))

bot.run(TOKEN)
