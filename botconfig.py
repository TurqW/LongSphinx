import yaml
import logging
import configmanager
log = logging.getLogger('LongSphinx.Config')
filename = 'config.yaml'
conf = configmanager.ConfigManager(filename)

def get_object(server_id, *hierarchy):
	found = conf.config['servers'][server_id]
	for level in hierarchy:
		try:
			found = found[level]
		except:
			log.error('Could not find {0} out of {1} on server {2}'.format(level, hierarchy, server_id))
	return found

def get_string(server_id, stringname):
	return get_object(server_id, 'strings', stringname)

def update_config():
	conf.update_config()
