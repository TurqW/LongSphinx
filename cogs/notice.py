from datetime import datetime
import logging

from discord import Cog, SlashCommandGroup, Option, AutocompleteContext

from botdb import BotDB
import botconfig as conf
from discordclasses.confirm import Confirm

dbname = "notices"
log = logging.getLogger('LongSphinx.Notice')


def update_notice(title, new_notice):
    async def update_notice_callback(interaction):
        curr_notices = load_notices(interaction.guild.id)
        curr_notices[title] = new_notice
        save_notices(curr_notices, interaction.guild.id)
        await interaction.response.edit_message(content="Notice updated.", embed=None, view=None)

    return update_notice_callback


def remove_notice(title):
    async def remove_notice_callback(interaction):
        curr_notices = load_notices(interaction.guild.id)
        if title in curr_notices:
            reply = f'Deleted notice {title}, former content was:\n```\n{curr_notices[title]["text"]}\n```'
            del curr_notices[title]
            save_notices(curr_notices, interaction.guild.id)
            await interaction.response.edit_message(content=reply, embed=None, view=None)

    return remove_notice_callback


def load_notices(server_id):
    with BotDB(conf.bot_name(), dbname) as db:
        if str(server_id) not in db:
            db[str(server_id)] = {}
        curr_notices = db[str(server_id)]
    return curr_notices


def save_notices(curr_notices, server_id):
    with BotDB(conf.bot_name(), dbname) as db:
        db[str(server_id)] = curr_notices


def get_latest(notice_list):
    try:
        return sorted(notice_list.values(), key=lambda notice: notice['created'])[-1]['text']
    except KeyError:
        return "No notices found on this server."


def notice_autocomplete(ctx: AutocompleteContext):
    curr_notices = load_notices(ctx.interaction.guild.id)
    return [key for key in curr_notices.keys() if ctx.value.lower() in key.lower()]


class Notices(Cog):
    def __init__(self, bot):
        self.bot = bot

    noticeGroup = SlashCommandGroup('notice', 'For server-wide announcements.')

    # I'd use slash command permissions, but they don't accept *permissions* just roles and users, for some reason.
    @noticeGroup.command(name='add', description='Create a new notice on this server.')
    async def add_notice(self, ctx,
                         title: Option(str, 'Title to find the notice by.'),
                         text: Option(str, 'Content of the notice.')):
        if ctx.user.guild_permissions.administrator:
            curr_notices = load_notices(ctx.guild.id)
            new_notice = {'text': text, 'created': datetime.utcnow().isoformat()}
            reply = f'Create notice "{title}"?\n'
            if title in curr_notices:
                reply = f'Update notice "{title}"?\n'
                reply += f'Old content:\n```\n{curr_notices[title]["text"]}\n```\n'
                new_notice['created'] = curr_notices[title]['created']
            reply += f'New content:\n>>> {text}'
            confirm_view = Confirm(update_notice(title, new_notice))
            await ctx.respond(reply, view=confirm_view, ephemeral=True)
        else:
            await ctx.respond("Only a server admin can add notices.", ephemeral=True)

    @noticeGroup.command(name='delete', description='Remove a notice from this server.')
    async def delete_notice(self, ctx,
                            title: Option(str, 'Delete which notice?', autocomplete=notice_autocomplete)):
        if ctx.user.guild_permissions.administrator:
            curr_notices = load_notices(ctx.guild.id)
            if title in curr_notices:
                reply = f'Delete notice {title}?\nFormer content was:\n```\n{curr_notices[title]["text"]}\n```'
                confirm_view = Confirm(remove_notice(title))
                await ctx.respond(reply, view=confirm_view, ephemeral=True)
            else:
                await ctx.respond(f'Notice "{title}" not found.', ephemeral=True)
        else:
            await ctx.respond("Only a server admin can delete notices.", ephemeral=True)

    @noticeGroup.command(name='read', description='Read a notice. Leave blank for most recent.')
    async def read_notice(self, ctx,
                          title: Option(str, 'Read which notice?', autocomplete=notice_autocomplete, required=False)):
        curr_notices = load_notices(ctx.guild.id)
        if not title:
            msg = '>>> ' + get_latest(curr_notices)
        elif title in curr_notices:
            msg = '>>> ' + curr_notices[title]['text']
        else:
            msg = f'Notice "{title}" not found. Try using the autocomplete.'
        await ctx.respond(msg)
