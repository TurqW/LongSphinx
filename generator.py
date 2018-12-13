import random
import logging
import yaml
from num2words import num2words
import re
import configmanager
import mcgenerator
log = logging.getLogger('LongSphinx.Generators')

conf = {}

def generate(name):
	if name.startswith('mc:'):
		#TODO: There may be a less hardcoded way to do this.
		return mcgenerator.generate(name[3:])
	if name.startswith('num:'):
		rangeends = name[4:].split('-')
		return num2words(random.randrange(int(rangeends[0]), int(rangeends[1])))
	parsed_name = name.split('.')
	generator = parsed_name[0]
	load_config(generator)
	if len(parsed_name) == 1:
		name_string = random.choice(conf[generator].config['root'])
	else:
		option_set = conf[generator].config
		for level in parsed_name[1:]:
			option_set = option_set[level]
		name_string = random.choice(option_set)
	return populate_string(name_string)
	

def populate_string(name_string):
	for toReplace in re.findall(r'{[\w.:-]+}', name_string):
		name_string = name_string.replace(toReplace, generate(toReplace[1:-1]), 1)
	return fix_articles(name_string)

def fix_articles(name_string):
	# relevant: https://stackoverflow.com/questions/2763750/how-to-replace-only-part-of-the-match-with-python-re-sub
	return re.sub(r"(^|\W)a( [aAeEiIoOuU](?!ni))", r'\1an\2', name_string)

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
