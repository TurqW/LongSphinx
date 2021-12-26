from PIL import Image
from io import BytesIO
from discord import slash_command, Cog, Option, File


def create_swatch(color):
    return Image.new('RGB', (200, 100), color)


def get_swatch(color):
    im = create_swatch(color)
    out = BytesIO()
    im.save(out, format='PNG')
    return BytesIO(out.getvalue())  # I know this looks dumb, but without it discord just sends a 0-byte file. ¯\_(ツ)_/¯


class ColorCommands(Cog):
    def __init__(self, bot):
        self.bot = bot

    @slash_command(name='color', description='Generate a color swatch from a hex code.', guild_ids=[489197880809095168])
    async def show_swatch(self, ctx, color_code: Option(str, 'Hex color string, such as #131071')):
        swatch = get_swatch(color_code)
        await ctx.respond('', file=File(swatch, filename=color_code + '.png'))
