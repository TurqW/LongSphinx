import yaml
import logging
import configmanager
log = logging.getLogger('LongSphinx.Config')
filename = 'config.yaml'
conf = configmanager.ConfigManager(filename)

def get_object(server, *hierarchy):
	try:
		found = conf.config['servers'][server.id]
	except KeyError:
		found = conf.config['servers']['default']
	for level in hierarchy:
		try:
			found = found[level]
		except:
			log.error('Could not find {0} out of {1} on server {2}'.format(level, hierarchy, server_id))
			return {}
	return found

def get_string(server, stringname):
	return get_object(server, 'strings', stringname)

def update_config():
	conf.update_config()
