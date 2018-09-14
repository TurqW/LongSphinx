import yaml
import os
import logging
log = logging.getLogger('CoreBot.Config')

lastmod = os.stat('config.yaml').st_mtime

with open("config.yaml", 'r') as stream:
	try:
		config = yaml.load(stream)
	except yaml.YAMLError as exc:
		sys.exit()


def get_object(server_id, *hierarchy):
	found = config['servers'][server_id]
	for level in hierarchy:
		found = found[level]
		if not found:
			log.error('Could not find {0} out of {1} on server {2}'.format(level, hierarchy, server_id))
	return found

def get_string(server_id, stringname):
	return get_object(server_id, 'strings', stringname)

def update_config():
	global lastmod
	global config
	newlastmod = os.stat('config.yaml').st_mtime
	if newlastmod > lastmod:
		log.info('New config found. Loading...')
		with open("config.yaml", 'r') as stream:
			try:
				config = yaml.load(stream)
				lastmod = newlastmod
			except yaml.YAMLError as exc:
				log.exception(exc)
				log.error('YAML invalid, sticking with version from {0}'.format(lastmod))
