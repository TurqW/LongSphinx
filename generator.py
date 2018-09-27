import random
import logging
import yaml
import configmanager
import namegen
log = logging.getLogger('LongSphinx.Generators')

conf = {}

def generate(name):
	if name == 'name':
		#TODO: There must be a less hardcoded way to do this.
		return namegen.generate_name()
	parsed_name = name.split('.')
	generator = parsed_name[0]
	if generator not in conf:
		conf[generator] = configmanager.ConfigManager('genConfig/{0}.yaml'.format(generator))
	conf[generator].update_config()
	if len(parsed_name) == 1:
		string = random.choice(conf[generator].config['root'])
	else:
		option_set = conf[generator].config
		for level in parsed_name[1:]:
			option_set = option_set[level]
		string = random.choice(option_set)
	return populate_string(string)
	

def populate_string(string):
	while '{' in string:
		start = string.find('{')
		end = string.find('}')
		replacement = generate(string[start+1:end])
		string = string[:start] + replacement + string[end+1:]
	return string
