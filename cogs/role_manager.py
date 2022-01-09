import logging
import random
from enum import Enum

from discord import Cog, ApplicationContext, AutocompleteContext, Interaction, Member, Role
from discord.commands import Option, slash_command
from discord.utils import find

import botconfig as conf
import utils
from discordclasses.confirm import Confirm

log = logging.getLogger('LongSphinx.RoleManager')


class OperationType(Enum):
    DELETE = 'removed'
    CREATE = 'added'
    RETAIN = 'kept'


# These two have to be outside the class so the autocomplete can reach them.
def get_roles(ctx: AutocompleteContext | ApplicationContext):
    rolesets = conf.get_object(ctx.interaction.guild, 'rolesets')
    roles = {}
    for roleset_name, roleset in rolesets.items():
        roles.update({role: roleset_name for role in roleset['roles'].keys()})
    valid_roles = {role_name: value for (role_name, value) in roles.items() if
                   role_name in [role.name for role in ctx.interaction.guild.roles]}
    return valid_roles


def roles_for_autocomplete(ctx: AutocompleteContext):
    return [role for role in get_roles(ctx).keys() if role.lower().startswith(ctx.value.lower())]


def do_role_changes(changes):
    async def role_change_callback(interaction: Interaction):
        await apply_changes(changes)
        await interaction.response.edit_message(content="Roles updated.", view=None)

    return role_change_callback


def get_role_changes(member: Member, role: Role, roleset_name):
    roleset = conf.get_object(member.guild, 'rolesets', roleset_name)
    changes = {'member': member, OperationType.DELETE: [], OperationType.CREATE: [], OperationType.RETAIN: []}
    if roleset['type'] == 'toggle':
        if member.get_role(role.id) is not None:
            changes[OperationType.DELETE].append(role)
        else:
            changes[OperationType.CREATE].append(role)
    else:
        changes[OperationType.CREATE].append(role)
        if 'secondaryRoles' in roleset['roles'][role.name]:
            changes[OperationType.CREATE].extend([
                find(lambda r: r.name.lower() == role_name.lower(), member.guild.roles)
                for role_name in roleset['roles'][role.name]['secondaryRoles']])
        remove_on_update = []
        if 'removeOnUpdate' in roleset:
            remove_on_update = roleset['removeOnUpdate']
        for current_role in member.roles:
            if current_role.name in roleset['roles'].keys() or current_role.name in remove_on_update:
                changes[OperationType.DELETE].append(current_role)
    for new_role in changes[OperationType.CREATE]:
        if new_role in changes[OperationType.DELETE]:
            changes[OperationType.RETAIN].append(new_role)
    for retained in changes[OperationType.RETAIN]:
        changes[OperationType.CREATE].remove(retained)
        changes[OperationType.DELETE].remove(retained)
    return changes


async def apply_changes(changes):
    if changes[OperationType.CREATE]:
        await changes['member'].add_roles(*changes[OperationType.CREATE])
    if changes[OperationType.DELETE]:
        await changes['member'].remove_roles(*changes[OperationType.DELETE])


def role_changes_to_string(changes):
    return '\n'.join([
        '\n'.join([f'{value.name} will be {key.value}.' for value in changes[key]])
        for key in OperationType if changes[key]
    ])


def get_randomables(server, roleset):
    role_names = conf.get_object(server, 'rolesets', roleset, 'roles')
    roles = [k for k, v in role_names.items() if not v or 'random' not in v or v['random']]
    valid_roles = [x for x in server.roles if x.name in roles]
    return valid_roles


async def random_role(member, roleset):
    role = random.choice(get_randomables(member.guild, roleset))
    changes = get_role_changes(member, role, roleset)
    await apply_changes(changes)
    return role


class RoleManager(Cog):
    def __init__(self, bot):
        self.bot = bot

    @slash_command(name='role', description='Change your self-assignable roles.', guild_ids=[489197880809095168])
    async def request_role(
            self,
            ctx: ApplicationContext,
            role_name: Option(str, "Pick a role!", autocomplete=roles_for_autocomplete)
    ):
        roles = get_roles(ctx)
        if role_name in roles.keys():
            roleset_name = roles[role_name]
            role = find(lambda r: r.name.lower() == role_name.lower(), ctx.guild.roles)
            changes = get_role_changes(ctx.user, role, roleset_name)
            confirm_view = Confirm(do_role_changes(changes))
            await ctx.respond(f"Changes:\n{role_changes_to_string(changes)}", view=confirm_view, ephemeral=True)

    @Cog.listener()
    async def on_member_join(self, member: Member):
        channel = utils.find_channel(conf.get_object(member.guild, 'greetingChannel'), member.guild)
        log.debug(f'{member.name} joined {member.guild}')
        if conf.get_object(member.guild, 'defaultRoleset'):
            role = await random_role(member, conf.get_object(member.guild, 'defaultRoleset'))
            msg = conf.get_string(member.guild, 'welcome').format(member.mention, role.name)
        else:
            msg = conf.get_string(member.guild, 'welcome').format(member.mention)
        await channel.send(msg)
