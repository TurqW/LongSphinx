from typing import List

from discord import Cog, Interaction, SelectOption, slash_command, Embed
from discord.ui import View

from persistence import botconfig as conf
from persistence.botdb import BotDB
from discordclasses.deletable import DeletableListView

DB_NAME = 'userconf'
CONFIG_MSG = 'You have these config keys defined. Deleting one will return that functionality to its default ' \
             'behavior. Creation and modification of these keys is handled within the relevant commands. '
NO_CONFIG_MSG = 'No config is defined for your user ID.'


def get_user_config(user_id):
    with BotDB(conf.bot_name(), DB_NAME) as db:
        if str(user_id) in db:
            return db[str(user_id)]
        else:
            return {}


def add_key(user_id, key, value):
    id_str = str(user_id)
    with BotDB(conf.bot_name(), DB_NAME) as db:
        if DB_NAME not in db:
            db[id_str] = {key: value}
        else:
            new_version = db[id_str]
            new_version[key] = value
            db[id_str] = new_version


def remove_key(user_id, key):
    id_str = str(user_id)
    with BotDB(conf.bot_name(), DB_NAME) as db:
        if id_str in db:
            new_version = db[id_str]
            if key in new_version:
                new_version.pop(key)
            db[id_str] = new_version


def get_key(user_id, key):
    userconf = get_user_config(user_id)
    if key in userconf:
        return userconf[key]
    return None


def create_embed(user_id, server):
    embed = Embed()
    for key, value in sorted(get_user_config(user_id).items()):
        embed.add_field(name=key, value=value)
    return embed if embed.fields else None


def macros_for_dropdown(interaction: Interaction):
    return [SelectOption(label=name) for name in get_user_config(interaction.user.id).keys()]


def create_deleter(user_id):
    id_str = str(user_id)

    def delete_keys(config_keys: List[str]):
        with BotDB(conf.bot_name(), DB_NAME) as db:
            if id_str in db:
                new_version = db[id_str]
                for name in config_keys:
                    new_version.pop(name)
                db[id_str] = new_version

    return delete_keys


async def list_refresher(interaction: Interaction, view: View):
    embed = create_embed(interaction.user.id, interaction.guild)
    await interaction.response.edit_message(content=CONFIG_MSG if embed else NO_CONFIG_MSG,
                                            embed=embed,
                                            view=view if embed else None)


class ConfigManager(Cog):
    def __init__(self, bot):
        self.bot = bot

    @slash_command(name='config', description='Show and manage config keys.')
    async def list_config(self, ctx):
        embed = create_embed(ctx.user.id, ctx.guild)
        view = DeletableListView(list_refresher, macros_for_dropdown, create_deleter(ctx.user.id)) if embed else None
        await ctx.respond(content=CONFIG_MSG if embed else NO_CONFIG_MSG, embed=embed, view=view, ephemeral=True)
