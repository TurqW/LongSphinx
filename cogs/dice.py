import random
from typing import List

import discord
from collections import OrderedDict

from discord import Cog, slash_command, Option, AutocompleteContext, SlashCommandGroup, Interaction, SelectOption
from discord.ui import View
from lark import Lark, Transformer
from lark.exceptions import LarkError
from botdb import BotDB

import botconfig as conf
from views.confirm import Confirm
from views.deletable import DeletableListView

dbname = 'macros'

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
        with BotDB(conf.bot_name(), dbname) as db:
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
        with BotDB(conf.bot_name(), dbname) as db:
            return db[user]
    except KeyError:
        return {}


def create_embed(user_id):
    embed = discord.Embed()
    for key, value in sorted(get_commands(str(user_id)).items()):
        embed.add_field(name=key, value=value)
    return embed


def macros_for_dropdown(interaction: Interaction):
    return [SelectOption(label=name) for name in get_commands(str(interaction.user.id))]


def create_deleter(user_id):
    id_str = str(user_id)

    def delete_rolls(names: List[str]):
        with BotDB(conf.bot_name(), dbname) as db:
            if id_str in db:
                new_version = db[id_str]
                for name in names:
                    new_version.pop(name.lower())
                db[id_str] = new_version

    return delete_rolls


async def list_refresher(interaction: Interaction, view: View):
    embed = create_embed(interaction.user.id)
    if embed.fields:
        await interaction.response.edit_message(content=interaction.user.mention + ' has these saved rolls.',
                                                embed=embed,
                                                view=view)
    else:
        await interaction.response.edit_message(content=interaction.user.mention + ' has no saved rolls.',
                                                embed=None,
                                                view=None)


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
    with BotDB(conf.bot_name(), dbname) as db:
        if id_str not in db:
            db[id_str] = {name: rolls}
        else:
            new_version = db[id_str]
            new_version[name] = rolls
            db[id_str] = new_version
    return f'{user.mention} has saved {rolls} as {name}'


def saver(label, rolls):
    async def save_callback(interaction):
        await interaction.response.edit_message(content=save_command(label, rolls, interaction.user), view=None)
    return save_callback


class RollCommands(Cog):
    def __init__(self, bot):
        self.bot = bot

    rollsGroup = SlashCommandGroup('rolls', 'Create and manage dice macros')

    @rollsGroup.command(name='save', description='Save a new dice macro or overwrite an old one.')
    async def save_command(self, ctx,
                           name: Option(str, 'Name of the macro. Letters and spaces only.'),
                           rolls: Option(str, 'The dice to roll. Separate with a comma. Modifiers allowed.')
                           ):
        await ctx.respond(save_command(name, rolls, ctx.user), ephemeral=True)

    @slash_command(name='roll', description='Roll the dice!')
    async def roll_dice(self, ctx, rolls: str,
                        label: Option(str, 'Would you like to label this roll?', required=False)):
        embed = discord.Embed()
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
            confirmer = Confirm(saver(label, rolls))
            await ctx.send_followup(f'Would you like to save {rolls} as {label}?', view=confirmer, ephemeral=True)

    # TODO: this can work like the reminders for deletions
    @rollsGroup.command(name='list', description='List your saved roll macros.')
    async def list_rolls(self, ctx):
        embed = create_embed(ctx.user.id)
        if embed.fields:
            await ctx.respond(content=ctx.user.mention + ' has these saved rolls.',
                              embed=embed,
                              view=DeletableListView(
                                  list_refresher,
                                  macros_for_dropdown,
                                  create_deleter(ctx.user.id)),
                              ephemeral=True)
        else:
            await ctx.respond(content=ctx.user.mention + ' has no saved rolls.', ephemeral=True)


def readme(**kwargs):
    return '''* `!roll NdM` or `!r NdM`: rolls a `M`-sided die `N` times. Multiple sets of dice can be used.
> Examples: `!roll 1d6`, `!roll 2d20+3`, `!roll 1d20, 3d6`.
* `!saveroll NdM: rollname`: saves NdM as rollname, so that you can roll it with just `!roll rollname`.
> Example: `!saveroll 1d20+5,1d8+3: hammer`
* `!rolls`: shows your saved rolls.
* `!clearroll rollname`: deletes a saved roll. There is no undo button.\n'''
