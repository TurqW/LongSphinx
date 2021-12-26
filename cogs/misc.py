from discord import Cog, slash_command, AutocompleteContext, Option, Member, Embed

import botconfig as conf
import generator


def gen_autocomplete(ctx: AutocompleteContext):
    available_gens = conf.get_object(ctx.interaction.guild, 'generators')
    return [name for name in available_gens if ctx.value.lower() in name.lower()]


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
        embed = Embed()
        embed.set_image(url=user.avatar.with_static_format('png').url)
        await ctx.respond(f"{user.mention}'s avatar!", embed=embed)

    @slash_command(name='serverpic', description="View this server's icon at a higher resolution.")
    async def get_server_pic(self, ctx):
        embed = Embed()
        embed.set_image(url=ctx.guild.icon.with_static_format('png').url)
        await ctx.respond(f"{ctx.guild.name}'s icon!", embed=embed)
