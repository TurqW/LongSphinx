import urllib.parse

async def get_link(argstring, conf, server, **kwargs):
	flag = conf.get_object(server, 'lmgtfyDefault')
	if argstring.startswith('-'):
		flag = argstring[1]
		argstring = argstring[2:].strip()
	query = {'q': argstring}
	if flag:
		query['s'] = flag
	url = '<http://lmgtfy.com/?' + urllib.parse.urlencode(query) + '>'
	return url

def readme(argstring, conf, server, **kwargs):
	flag = conf.get_object(server, 'lmgtfyDefault')
	if not flag:
		flag = 'g'
	return '''* `!{} <query>`: Provides an easy LMGTFY link with a single command.
Supports flags to use alternative search engines. Start your <query> with:
> `-a` AOL
> `-b` Bing
> `-d` DuckDuckGo
> `-g` Google
> `-k` Ask
> `-y` Yahoo
This server defaults to: `-{}`'''.format(argstring, flag)