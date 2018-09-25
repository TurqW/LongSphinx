import random
import logging
import yaml
import configmanager
log = logging.getLogger('LongSphinx.Generators')

conf = {}

#TODO: incorporate the name generator?
#TODO: configure list of available generators per-server
def generate(name):
	parsed_name = name.split('.')
	generator = parsed_name[0]
	if generator not in conf:
		conf[generator] = configmanager.ConfigManager('genConfig/{0}.yaml'.format(generator))
	conf[generator].update_config()
	if len(parsed_name) == 1:
		string = random.choice(conf[generator].config['root'])
	else:
		string = random.choice(conf[generator].config[parsed_name[1]])
	return populate_string(string)
	

def populate_string(string):
	while '{' in string:
		start = string.find('{')
		end = string.find('}')
		replacement = generate(string[start+1:end])
		string = string[:start] + replacement + string[end+1:]
	return string
