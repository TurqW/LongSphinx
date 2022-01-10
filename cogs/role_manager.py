import logging
import random
from enum import Enum

from discord import ButtonStyle, Interaction, Button, SelectOption, Cog, ApplicationContext, AutocompleteContext, \
    Member, Role
from discord.commands import Option, slash_command
from discord.ui import button, View, Select
from discord.utils import find

from persistence import botconfig as conf
from discordclasses import utils
from discordclasses.confirm import Confirm

log = logging.getLogger('LongSphinx.RoleManager')


class OperationType(Enum):
    DELETE = 'removed'
    CREATE = 'added'
    RETAIN = 'kept'


# These two have to be outside the class so the autocomplete can reach them.
def get_roles(ctx):
    return get_roles_itn(ctx.interaction)


def get_roles_itn(interaction):
    rolesets = conf.get_object(interaction.guild, 'rolesets')
    roles = {}
    for roleset_name, roleset in rolesets.items():
        roles.update({role: roleset_name for role in roleset['roles'].keys()})
    valid_roles = {role_name: value for (role_name, value) in roles.items() if
                   role_name in [role.name for role in interaction.guild.roles]}
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
    return sanitize_changes(changes)


def sanitize_changes(changes):
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


class RolesView(View):
    def __init__(self, options):
        super().__init__()
        self.dropdown = None
        self.dropdown = Select(
            placeholder="Select a role",
            max_values=1,
            options=options
        )
        self.add_item(self.dropdown)

    @button(label="Toggle role", row=2, style=ButtonStyle.grey)
    async def add(self, _: Button, interaction: Interaction):
        role_name = self.dropdown.values[0]
        roles = get_roles_itn(interaction)
        roleset_name = roles[role_name]
        role = find(lambda r: r.name.lower() == role_name.lower(), interaction.guild.roles)
        changes = get_role_changes(interaction.user, role, roleset_name)
        confirm_view = Confirm(do_role_changes(changes))
        await interaction.response.send_message(f"Changes:\n{role_changes_to_string(changes)}",
                                                view=confirm_view, ephemeral=True)

    async def on_timeout(self):
        self.clear_items()
        await self.interaction.edit_original_message(view=self)


class RoleManager(Cog):
    def __init__(self, bot):
        self.bot = bot

    @slash_command(name='role', description='Change your self-assignable roles.')
    async def request_role(
            self,
            ctx: ApplicationContext,
            role_name: Option(str, "Name of a role to toggle (optional)", autocomplete=roles_for_autocomplete,
                              required=False)
    ):
        roles = get_roles(ctx)
        if role_name and role_name in roles.keys():
            roleset_name = roles[role_name]
            role = find(lambda r: r.name.lower() == role_name.lower(), ctx.guild.roles)
            changes = get_role_changes(ctx.user, role, roleset_name)
            confirm_view = Confirm(do_role_changes(changes))
            await ctx.respond(f"Changes:\n{role_changes_to_string(changes)}", view=confirm_view, ephemeral=True)
        elif 1 < len(roles) < 25:
            role_options = [SelectOption(label=role_name, value=role_name) for role_name in get_roles(ctx).keys()]
            view = RolesView(role_options)
            view.interaction = await ctx.respond('Have a choice!', view=view, ephemeral=True)
        else:
            await ctx.respond('The following roles are self-assignable on this server, use this command with a '
                              'role_name:\n '
                              + ', '.join(role for role in sorted(roles.keys())), ephemeral=True)

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
