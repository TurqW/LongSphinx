import random
from collections import OrderedDict
from datetime import datetime, timedelta
from typing import List

from discord import Cog, slash_command, Option, SlashCommandGroup, Interaction, SelectOption, message_command, Embed
from discord.ui import View
from lark import Lark, Transformer
from lark.exceptions import LarkError

import botconfig as conf
from botdb import BotDB
from cogs import userconfig
from discordclasses.confirm import Confirm
from discordclasses.deletable import DeletableListView

DB_NAME = 'macros'
SUPPRESS_SAVE_CONFIG_KEY = 'Dice.SuppressSaveSuggestionUntil'

parser = Lark(r"""
%import common.WS
%ignore WS
%import common.DIGIT

POSINT : DIGIT DIGIT*
sign : /[+-]/
rollset : expression ("," expression)*
expression : die -> roll
			| POSINT -> mod
			| expression sign expression -> math
die : [POSINT] _DSEPARATOR POSINT
count : POSINT
size : POSINT
_DSEPARATOR : "d"
""", start='rollset')


class RollsetTransformer(Transformer):
    def rollset(self, list):
        results = OrderedDict()
        for item in list:
            key = item['name']
            iterator = 0
            while key in results:
                iterator += 1
                key = item['name'] + ' (' + str(iterator) + ')'
            if '+' not in item['description']:
                results[key] = '**' + str(item['value']) + '**'
            else:
                results[key] = item['description'] + ' = **' + str(item['value']) + '**'
        return results

    def die(self, list):
        try:
            count = int(list[0])
            size = int(list[1])
        except IndexError:
            count = 1
            size = int(list[0])
        if count > 1000:
            raise Exception('Too many dice, blocking to avoid DDOS')
        results = []
        for i in range(count):
            if size == 0:
                results.append(0)
            else:
                results.append(random.randint(1, size))
        description = '(' + '+'.join([str(i) for i in results]) + ')'
        name = str(count) + 'd' + str(size)
        return {'name': name, 'description': description, 'value': sum(results)}

    def roll(self, list):
        return list[0]

    def math(self, list):
        name = "".join([a['name'] for a in list])
        description = "".join([a['description'] for a in list])
        value = list[0]['value'] + list[1]['value'] * list[2]['value']
        return {'name': name, 'description': description, 'value': value}

    def mod(self, num):
        return {'name': str(num[0]), 'description': str(num[0]), 'value': int(num[0])}

    def sign(self, sign):
        if sign[0] == '+':
            return {'name': '+', 'description': '+', 'value': 1}
        else:
            return {'name': '-', 'description': '-', 'value': -1}

    def POSINT(self, num):
        return int(''.join(num))

    def INT(self, num):
        return int(''.join(num))


def roll_command(user, command):
    if not command:
        command = 'd20'
    name = ''
    if ':' in command:
        command, name = command.split(':')
        name = name.strip()
    else:
        with BotDB(conf.bot_name(), DB_NAME) as db:
            if user in db:
                macros = db[user]
                for key in sorted(macros.keys(), key=len):
                    # For prefix matching, you want to match to the shortest possible match so all matches can be hit
                    if key.startswith(command.lower()):
                        if not name:
                            name = key
                        command = macros[key]
        # TODO this should be way more specific
    return name, RollsetTransformer().transform(parser.parse(command))


def stringy_mod(modifier):
    if modifier > 0:
        return '+' + str(modifier)
    if modifier < 0:
        return str(modifier)
    return ''


def get_commands(user):
    try:
        with BotDB(conf.bot_name(), DB_NAME) as db:
            return db[user]
    except KeyError:
        return {}


def create_macro_list_embed(user_id, server):
    embed = Embed()
    for key, value in sorted(get_commands(str(user_id)).items()):
        embed.add_field(name=key, value=value)
    return embed if embed.fields else None


def macros_for_dropdown(interaction: Interaction):
    return [SelectOption(label=name) for name in get_commands(str(interaction.user.id))]


def create_deleter(user_id):
    id_str = str(user_id)

    def delete_rolls(names: List[str]):
        with BotDB(conf.bot_name(), DB_NAME) as db:
            if id_str in db:
                new_version = db[id_str]
                for name in names:
                    new_version.pop(name.lower())
                db[id_str] = new_version

    return delete_rolls


async def list_refresher(interaction: Interaction, view: View):
    embed = create_macro_list_embed(interaction.user.id, interaction.guild)
    await interaction.response.edit_message(content=interaction.user.mention + ' has these saved rolls.',
                                            embed=embed,
                                            view=view if embed else None)


def save_command(name, rolls, user):
    name = name.strip().lower()
    rolls = rolls.strip().lower()
    id_str = str(user.id)
    try:
        parser.parse(rolls)
    except LarkError:
        return f'Command "{rolls}" was not valid.'
    if any(char.isdigit() for char in name):
        return f'Name "{name}" was not valid. Please do not include any numbers or special characters.'
    with BotDB(conf.bot_name(), DB_NAME) as db:
        if id_str not in db:
            db[id_str] = {name: rolls}
        else:
            new_version = db[id_str]
            new_version[name] = rolls
            db[id_str] = new_version
    return f'You have saved {rolls} as {name}'


def saver(label, rolls):
    async def save_callback(interaction):
        await interaction.response.edit_message(content=save_command(label, rolls, interaction.user), view=None)

    return save_callback


async def suppress_autosave(interaction):
    userconfig.add_key(interaction.user.id, SUPPRESS_SAVE_CONFIG_KEY, datetime.now() + timedelta(hours=24))
    await interaction.response.edit_message(content="Ok, I won't ask this for a day. You can undo this by deleting "
                                                    "the `Dice.SuppressSaveSuggestionUntil` config key in the `/config`"
                                                    " command.", view=None)


async def never_show_autosave(interaction):
    userconfig.add_key(interaction.user.id, SUPPRESS_SAVE_CONFIG_KEY, datetime.now() + timedelta(days=1000 * 365))
    await interaction.response.edit_message(content="Ok, I won't ask this any more. You can undo this by deleting the "
                                                    "`Dice.SuppressSaveSuggestionUntil` config key in the `/config` "
                                                    " command.", view=None)


def sanitize_suppress_save_config(user_id, suppress_until):
    if suppress_until and suppress_until < datetime.now():
        userconfig.remove_key(user_id, SUPPRESS_SAVE_CONFIG_KEY)


class RollCommands(Cog):
    def __init__(self, bot):
        self.bot = bot

    rollsGroup = SlashCommandGroup('rolls', 'Create and manage dice macros')

    @rollsGroup.command(name='save', description='Save a new dice macro or overwrite an old one.')
    async def save_macro(self, ctx,
                         name: Option(str, 'Name of the macro. Letters and spaces only.'),
                         rolls: Option(str, 'The dice to roll. Separate with a comma. Modifiers allowed.')
                         ):
        await ctx.respond(save_command(name, rolls, ctx.user), ephemeral=True)

    @slash_command(name='roll', description='Roll the dice!')
    async def roll_dice(self, ctx, rolls: str,
                        label: Option(str, 'Would you like to label this roll?', required=False)):
        embed = Embed()
        command_name, results = roll_command(str(ctx.user.id), rolls)
        for key, value in results.items():
            embed.add_field(name=key, value=value)
        follow_up = False
        if label:
            embed.title = label
            if not command_name and not any(char.isdigit() for char in label):
                follow_up = True
        else:
            label = rolls
            if command_name:
                embed.title = command_name
                label = command_name
        msg = ctx.user.mention + ' rolled ' + label + '!'
        await ctx.respond(msg, embed=embed)
        if follow_up:
            suppress_until = userconfig.get_key(ctx.user.id, SUPPRESS_SAVE_CONFIG_KEY)
            sanitize_suppress_save_config(ctx.user.id, suppress_until)
            if not suppress_until or suppress_until < datetime.now():
                confirmer = Confirm(saver(label, rolls),
                                    middle_callback=suppress_autosave,
                                    middle_label="Don't show for 24H",
                                    cancel_callback=never_show_autosave,
                                    cancel_label="Never show this")
                await ctx.respond(f'Would you like to save {rolls} as {label}?', view=confirmer, ephemeral=True)

    @rollsGroup.command(name='list', description='List your saved roll macros.')
    async def list_rolls(self, ctx):
        embed = create_macro_list_embed(ctx.user.id, ctx.guild)
        if embed:
            msg = ctx.user.mention + ' has these saved rolls.'
            view = DeletableListView(list_refresher, macros_for_dropdown, create_deleter(ctx.user.id))
        else:
            msg = ctx.user.mention + ' has no saved rolls.'
            view = None
        await ctx.respond(content=msg, embed=embed, view=view, ephemeral=True)

    @message_command(name='Save this roll', description='Use this on a roll result to save it to your macros.')
    async def save_from_message(self, ctx, message):
        embed = None
        if message.embeds:
            embed = message.embeds[0]
        if not embed or not embed.title or not embed.fields:
            await ctx.respond('Sorry, you can only use this command on a labeled roll result.', ephemeral=True)
            return
        msg = save_command(embed.title, ', '.join([field.name for field in embed.fields]), ctx.user)
        await ctx.respond(msg, ephemeral=True)
