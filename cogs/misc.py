import logging
from random import sample

from discord import Cog, slash_command, AutocompleteContext, Option, Member, Object, NotFound, Forbidden, Role
from mwclient import Site

import botconfig as conf
import generator
import utils
from discordclasses.embed import DefaultEmbed

log = logging.getLogger('LongSphinx.Misc')
USER_AGENT = 'LongSphinx/0.1 (longsphinx@mage.city)'


def gen_autocomplete(ctx: AutocompleteContext):
    available_gens = conf.get_object(ctx.interaction.guild, 'generators')
    return [name for name in available_gens if ctx.value.lower() in name.lower()]


def wikis_autocomplete(ctx: AutocompleteContext):
    available_wikis = conf.get_object(ctx.interaction.guild, 'mwSites')
    return [name for name in available_wikis if ctx.value.lower() in name.lower()]


class MiscCommands(Cog):
    def __init__(self, bot):
        self.bot = bot

    @slash_command(name='gen', description='Use one of my many Thing Generators!')
    async def generate(self, ctx,
                       name: Option(str, 'Which generator?', autocomplete=gen_autocomplete),
                       count: Option(int, 'How many? Default 1.', required=False) = 1,
                       public: Option(bool, 'Should others see output? Default false.', required=False) = False
                       ):
        if name in conf.get_object(ctx.guild, 'generators'):
            await ctx.respond(
                '\n'.join([generator.extract_text(generator.generate(name)) for _ in range(count)]),
                ephemeral=not public)
        else:
            await ctx.respond(f"{name} is not a recognized generator.")

    @slash_command(name='pic', description="View a user's profile picture at a higher resolution.")
    async def get_pic(self, ctx, user: Member):
        embed = DefaultEmbed(ctx.guild)
        embed.set_image(url=user.avatar.with_static_format('png').url)
        await ctx.respond(f"{user.mention}'s avatar!", embed=embed)

    @slash_command(name='serverpic', description="View this server's icon at a higher resolution.")
    async def get_server_pic(self, ctx):
        embed = DefaultEmbed(ctx.guild)
        embed.set_image(url=ctx.guild.icon.with_static_format('png').url)
        await ctx.respond(f"{ctx.guild.name}'s icon!", embed=embed)

    @slash_command(name='search', description='Search a configured MediaWiki instance.')
    async def search(self, ctx, site_name: Option(str, 'What wiki to search', autocomplete=wikis_autocomplete),
                     query: str):
        mw_options = conf.get_object(ctx.guild, 'mwSites')
        if site_name not in mw_options:
            return await ctx.respond(f'"{site_name}" is not a valid search source on this server.')
        site = Site(mw_options[site_name]['url'], path=mw_options[site_name]['path'], clients_useragent=USER_AGENT)
        results = site.search(query)
        title = results.next().get('title').replace(' ', '_')
        await ctx.respond(f'First result for "{query}":\n' +
                          str(f'https://{mw_options[site_name]["url"]}{mw_options[site_name]["pagePath"]}{title}'))

    @slash_command(name='ban', description='Ban a user from this guild. Only works if you have ban permissions.')
    async def ban(self, ctx,
                  member: Option(Member, 'Ban a member of the server.', required=False),
                  userid: Option(int, 'Ban any user by id.', required=False)
    ):
        if not ctx.user.guild_permissions.ban_members:
            await ctx.respond(conf.get_string(ctx.user, 'insufficientUserPermissions'), ephemeral=True)
            return
        if not member and not userid:
            await ctx.respond('Must enter at least one of member or userid.', ephemeral=True)
        if member:
            user = member
        else:
            user = Object(userid)
        try:
            await ctx.guild.ban(user)
        except NotFound:
            await ctx.respond(f'User {user.id} could not be found', ephemeral=True)
            return
        except Forbidden:
            log.exception(f'Could not ban {user.id} from server {ctx.guild.id}. Check permissions.')
            await ctx.respond('Ban failed due to permissions issue. Do I have the "ban" permission?', ephemeral=True)
            return
        await ctx.respond(f'Banned user {user.id}.')

    @slash_command(name='pick', description='Makes a decision for you')
    async def pick(self, ctx,
                   number: Option(int, 'How many to pick of the given choices.', required=False) = 1,
                   options: Option(str, 'What to pick from. Separated by spaces or commas.', required=False) = None,
                   role: Option(Role, 'Pick a random member that has a given role on this server.', required=False) = None):
        embed = DefaultEmbed(ctx.guild)
        if options:
            if ',' in options:
                optionset = options.split(',')
            else:
                optionset = options.split()
            embed.set_footer(text='Options were:\n> ' + '\n> '.join(optionset))
        elif role:
            optionset = [member.mention for member in role.members]
            embed.set_footer(text=f'Randomly selected from all members with the {role.name} role.')
            if role.is_default():
                embed.set_footer(text='Randomly selected from all members of this server.')
        else:
            await ctx.respond('Sorry, you have to give me something to pick from, either options or a role.',
                              ephemeral=True)
            return
        if number < 1:
            await ctx.respond('I have chosen nothing. I award you no points, and may the gods have mercy on your soul.',
                              ephemeral=True)
            return
        if number > len(optionset):
            number = len(optionset)
        embed.insert_field_at(0, name='Chosen:', value='**' + '**\n**'.join(sample(optionset, number)) + '**', inline=False)
        await ctx.respond('I have chosen!', embed=embed)

    @Cog.listener('on_member_remove')
    async def on_member_remove(self, member):
        channel = utils.find_channel(conf.get_object(member.guild, 'leavingChannel'), member.guild)
        if channel:
            msg = conf.get_string(member.guild, 'left').format(member.name)
            await channel.send(msg)
