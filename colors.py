from PIL import Image
from io import BytesIO

def create_swatch(color):
	return Image.new('RGB', (200, 100), color)

def get_swatch(color):
	im = create_swatch(color)
	out = BytesIO()
	im.save(out, format='PNG')
	return BytesIO(out.getvalue()) #I know this looks dumb, but without it discord just sends a 0-byte file. ¯\_(ツ)_/¯

async def show_swatch(input, client, channel, **kwargs):
	swatch = get_swatch(input)
	await client.send_file(channel, swatch, filename=input + '.png')

def readme():
	return '* `!color #hex`: Shows a color swatch of the color denoted by the hex sequence. Example: `!color #131071`\n'