from num2words import num2words
from persistence import configmanager
import copy
import logging
from generators import mcgenerator
import random
import re

log = logging.getLogger('LongSphinx.Generators')

genConfigs = {}


def generate(name, seed=None):
    if seed:
        random.seed(seed)
    if name.startswith('mc.'):
        # TODO: There may be a less hardcoded way to do this.
        result = {'text': mcgenerator.generate(name[3:])}
    elif name.startswith('num.'):
        rangeends = name.strip("num. ").split('-')
        result = {'text': num2words(random.randrange(int(rangeends[0]), int(rangeends[1])))}
    else:
        parsed_name = name.split('.')
        generator = parsed_name[0]
        load_config(generator)
        modifier = ''
        if '/' in parsed_name[-1]:
            modifier = parsed_name[-1].split('/')[-1]
            parsed_name[-1] = parsed_name[-1].split('/')[0]
        if len(parsed_name) == 1:
            result = copy.deepcopy(random.choice(genConfigs[generator].config['root']))
        else:
            option_set = genConfigs[generator].config
            for level in parsed_name[1:]:
                option_set = option_set[level]
            result = copy.deepcopy(random.choice(option_set))
        if modifier:
            if modifier in result:
                result = result[modifier]
            else:
                if modifier == 'plural':
                    result['text'] += 's'
    return populate(result)


def load_config(name):
    if name not in genConfigs:
        genConfigs[name] = configmanager.ConfigManager(f'genConfig/{name}.yaml')
    genConfigs[name].update_config()


def populate(gen_dict):
    for key in (key for key in gen_dict.keys() if key != 'text' and isinstance(gen_dict[key], str)):
        gen_dict[key] = generate(gen_dict[key])
    return gen_dict


def extract_text(gen_dict):
    random.seed()  # Doing this here so that it'll randomize the seed after each call
    text = gen_dict['text']
    fillings = {}
    for key in (key for key in gen_dict.keys() if key != 'text' and key[0] != '.'):
        fillings[key] = extract_text(gen_dict[key])
    return fix_articles(text.format(**fillings))


def fix_articles(text):
    # relevant: https://stackoverflow.com/questions/2763750/how-to-replace-only-part-of-the-match-with-python-re-sub
    return re.sub(r"(^|\W)a( [aAeEiIoOuU](?!ni))", r'\1an\2', text)

