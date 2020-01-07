from PIL import Image
from io import BytesIO
import random

def create_swatch(color):
	return Image.new('RGB', (200, 100), color)

def get_swatch(color):
	im = create_swatch(color)
	out = BytesIO()
	im.save(out, format='PNG')
	return BytesIO(out.getvalue()) #I know this looks dumb, but without it discord just sends a 0-byte file. ¯\_(ツ)_/¯

async def show_swatch(input, client, channel, **kwargs):
	if not input:
		input = "#%06x" % random.randint(0, 0xFFFFFF)
	swatch = get_swatch(input)
	await client.send_file(channel, swatch, filename=input + '.png')
	return input

def readme(input, **kwargs):
	return '''* `!{0} #hex`: Shows a {0} swatch of the {0} denoted by the hex sequence.
> Example: `!{0} #131071`\n'''.format(input)
