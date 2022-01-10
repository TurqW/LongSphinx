from persistence import configmanager
import sys
from mcgenerator import MName

mcDataPath = 'genConfig/mcSources/'
conf = {}


def generate(name):
    if name not in conf:
        conf[name] = configmanager.ConfigManager(f'{mcDataPath}{name}.yaml')
    conf[name].update_config()
    return MName(conf[name].config).new()


def analyze(name):
    if name not in conf:
        conf[name] = configmanager.ConfigManager(f'{mcDataPath}{name}.yaml')
    conf[name].update_config()
    gen = MName(conf[name].config)
    singles = {key: value[0] for (key, value) in gen.mcd.d.items() if len(value) <= 1}
    chains = []
    chainlen = gen.chainlen * -1
    for key, value in singles.items():
        while (key + value)[chainlen:] in singles:
            value += singles[(key + value)[chainlen:]]
        chains.append(key + value)
    chains = [chain for chain in chains if not any(chain in o and chain != o for o in chains) and len(chain) > 3]
    print(chains)


if len(sys.argv) > 1:
    analyze(sys.argv[1])
