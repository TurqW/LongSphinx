import random
import logging
import yaml
import configmanager
import mcgenerator
log = logging.getLogger('LongSphinx.Generators')

conf = {}

def generate(name):
	if name.startswith('mc:'):
		#TODO: There may be a less hardcoded way to do this.
		return mcgenerator.generate(name[3:])
	parsed_name = name.split('.')
	generator = parsed_name[0]
	load_config(generator)
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

def load_config(name):
	if name not in conf:
		conf[name] = configmanager.ConfigManager('genConfig/{0}.yaml'.format(name))
	conf[name].update_config()

def readme(generators):
	msg = ''
	for gen_name in generators:
		load_config(gen_name)
		msg += '* `!' + gen_name + '`: '
		msg += conf[gen_name].config['description']
		msg += '\n'
	return msg
