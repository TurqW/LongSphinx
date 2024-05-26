import asyncio
import logging
from uuid import uuid4

from discord.ui import View
from datetime import datetime, timezone
from discord import slash_command, Option, Interaction, Embed, Cog, Member, ButtonStyle, SelectOption
from discordclasses.confirm import Confirm
from discordclasses.deletable import DeletableListView

from persistence import botconfig as conf
from persistence.botdb import BotDB
import feedparser

DB_NAME = 'feeds'
DB_KEY = '0'
CHANNEL_KEY = 0
URL_KEY = 1
PUBLISHED_KEY = 2
NO_FEEDS_MESSAGE = "No feeds configured"
scheduled_tasks = {}
log = logging.getLogger('LongSphinx.Rep')


def load_feeds():
    with BotDB(conf.bot_name(), DB_NAME) as db:
        if DB_KEY in db:
            return db[DB_KEY]
        else:
            return {}


def save_feeds(feeds):
    with BotDB(conf.bot_name(), DB_NAME) as db:
        db[DB_KEY] = feeds


def add_one_feed(channel, url):
    feeds = load_feeds()
    feed_id = str(uuid4())
    # Set the last seen to later
    # next time it's processed, it'll be set back to the datetime of the latest entry
    # If the times are synched correctly, this could theoretically mean we miss any posts made in the first 5 minutes
    feeds[feed_id] = (channel.id, url, datetime.now(timezone.utc).replace(year=3000))
    save_feeds(feeds)
    return feed_id


def update_feed(id, feed):
    feeds = load_feeds()
    feeds[id] = feed
    save_feeds(feeds)


def delete_feed(feed_id):
    feeds = load_feeds()
    if feed_id in feeds:
        feeds.pop(feed_id)
        save_feeds(feeds)


async def process_feed(channel, id, feed, force_backlog=0):
    try:
        NewsFeed = feedparser.parse(feed[URL_KEY])
        for entry in NewsFeed.entries:
            if not hasattr(entry, 'published_parsed') and hasattr(entry, 'updated_parsed'):
                entry.published_parsed = entry.updated_parsed
        if len(NewsFeed.entries) > 0:
            lastNew = len(NewsFeed.entries) - 1
            while lastNew >= force_backlog and datetime(*(NewsFeed.entries[lastNew].published_parsed[0:6]), tzinfo=timezone.utc) <= feed[PUBLISHED_KEY]:
                lastNew -= 1
            if lastNew >= 0:
                await publish(channel, NewsFeed.feed.title, NewsFeed.entries[0:lastNew + 1])
            feed = (feed[0], feed[1], datetime(*(NewsFeed.entries[0].published_parsed[0:6]), tzinfo=timezone.utc))
            update_feed(id, feed)
    except Exception as e:
        log.error("Failed to publish feed: " + str(feed) + " because " + str(e))


async def publish(channel, source, entries):
    for entry in reversed(entries):
        embed = Embed()
        embed.title = entry.title
        embed.url = entry.link
        embed.timestamp = datetime(*(entry.published_parsed[0:6]), tzinfo=timezone.utc)
        embed.color = conf.get_object(channel.guild, 'embedColor')
        await channel.send(f"New post from {source}:", embed=embed)


def add_feed(channel, url, backlog):
    async def add_feed_callback(interaction: Interaction):
        id = add_one_feed(channel, url)
        await interaction.response.edit_message(content="Feed added.", view=None)
        feed = load_feeds()[id]
        await process_feed(channel, id, feed, backlog)

    return add_feed_callback


async def list_refresher(interaction: Interaction, view: View):
    msg = feeds_list_message(interaction.channel.id)
    await interaction.response.edit_message(
        content=msg,
        view=view if msg != NO_FEEDS_MESSAGE else None
    )


def feeds_for_dropdown(interaction: Interaction):
    """
     Used by the DeletableListView
     @param interaction:
     @return: list of SelectOptions with that user's reminders
     """
    return [SelectOption(label=feed[URL_KEY], value=key) for (key, feed) in
            load_feeds().items() if feed[CHANNEL_KEY] == interaction.channel.id]


def delete_feeds(ids):
    """
    Used by the DeletableListView
    @param ids: list of ids to delete
    @return:
    """
    for feed_id in ids:
        delete_feed(feed_id)


def feeds_list_message(channel_id):
    all_feeds = load_feeds().values()
    string_list = [feed[URL_KEY] for feed in load_feeds().values() if feed[CHANNEL_KEY] == channel_id]
    if string_list:
        return '\n'.join(string_list)
    else:
        return NO_FEEDS_MESSAGE


class Feeds(Cog):
    def __init__(self, bot):
        self.bot = bot

    @Cog.listener()
    async def on_ready(self):
        asyncio.get_event_loop().create_task(self.process_feeds())

    async def process_feeds(self):
        while True:
            for key, feed in load_feeds().items():
                channel = self.bot.get_channel(feed[CHANNEL_KEY])
                await process_feed(channel, key, feed)
            await asyncio.sleep(5)

    @slash_command(name='rssadd', description='add an RSS feed to broadcast in the current channel.')
    async def add_rss_feed(
            self, ctx,
            url: Option(str, 'RSS URL'),
            backlog: Option(int, 'Number of recent entries to immediately publish. Default: 0', default=0)
    ):
        permissions = ctx.channel.permissions_for(ctx.user)
        if not permissions.manage_messages:
            await ctx.respond(conf.get_string(ctx.user, 'insufficientUserPermissions'), ephemeral=True)
            return
        permissions2 = ctx.channel.permissions_for(ctx.me)
        if not permissions2.send_messages or not permissions2.embed_links:
            await ctx.respond("I need permissions to both send messages and embed links in this channel in order to follow an RSS feed.", ephemeral=True)
            return
        confirm_view = Confirm(add_feed(ctx.channel, url, backlog))
        try:
            NewsFeed = feedparser.parse(url)
            embed = Embed()
            embed.title = NewsFeed.feed.title
            embed.description = NewsFeed.feed.subtitle
            embed.add_field(name="Latest Entry", value=NewsFeed.entries[0].title)
            embed.url = NewsFeed.feed.link
            await ctx.respond(f"Add feed {url} to this channel, publishing {backlog} recent entries?", embed=embed,
                              view=confirm_view, ephemeral=True)
        except:
            await ctx.respond(
                f"Unable to parse feed at {url}.\nMake sure your link points to the RSS feed, not the main site.",
                ephemeral=True)

    @slash_command(name='rsslist', description='List and remove RSS feeds for the current channel.')
    async def list_feeds(self, ctx):
        permissions = ctx.channel.permissions_for(ctx.user)
        if not permissions.manage_messages:
            await ctx.respond(conf.get_string(ctx.user, 'insufficientUserPermissions'), ephemeral=True)
            return
        msg = feeds_list_message(ctx.channel.id)
        view = None if msg == NO_FEEDS_MESSAGE else DeletableListView(list_refresher, feeds_for_dropdown,
                                                                      delete_feeds)
        await ctx.respond(msg, view=view, ephemeral=True)
