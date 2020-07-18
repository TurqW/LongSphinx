from mwclient import Site
import urllib.parse

ua = 'LongSphinx/0.1 (longsphinx@mage.city)'


async def search(server, argstring, conf, **kwargs):
	mwOptions = conf.get_object(server, 'mwSites')
	siteName, query = argstring.split(' ', 1)
	if siteName not in mwOptions:
		return f'"{siteName}" is not a valid search source on this server.'
	site = Site(mwOptions[siteName]['url'], path=mwOptions[siteName]['path'], clients_useragent=ua)
	results = site.search(query)
	title = results.next().get('title').replace(' ', '_')
	return str(f'https://{mwOptions[siteName]["url"]}{mwOptions[siteName]["pagePath"]}{title}')

def readme(server, conf, **kwargs):
	msg = 'Searches a mediawiki instance and returns a link to the first result. Enabled instances on this server:\n'
	for wiki, deets in conf.get_object(server, 'mwSites').items():
		msg += f' * {wiki}: {deets["url"]}\n'
	return msg
