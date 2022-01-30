import logging

from persistence.configmanager import ConfigManager

log = logging.getLogger('LongSphinx.Config')


def __init__(filename='../config.yaml', new_bot_name='Universal'):
    global conf
    conf = ConfigManager(filename, new_bot_name)


def get_object(server, *hierarchy):
    try:
        found = conf.config['servers'][str(server.id)]
    except (KeyError, AttributeError):
        found = conf.config['servers']['default']
    for level in hierarchy:
        try:
            found = found[level]
        except KeyError:
            log.error('Could not find {0} out of {1} on server {2}'.format(level, hierarchy,
                                                                           server.id if hasattr(server,
                                                                                                'id') else 'default'))
            return {}
    return found


def get_string(server, stringname):
    return get_object(server, 'strings', stringname)


def bot_name():
    return conf.botName


async def update_config(**kwargs):
    conf.update_config()
