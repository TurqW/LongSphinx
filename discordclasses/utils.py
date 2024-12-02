import asyncio
import os

fullGaugeChar = '='
emptyGaugeChar = ' '


def check_path(name):
    if not os.path.exists(name):
        os.makedirs(name)


def draw_gauge(current_value, max_value):
    return '[' + fullGaugeChar * current_value + emptyGaugeChar * (max_value - current_value) + ']'


def find_self_member(client, server):
    return next(member for member in server.members if member.id == client.user.id)


def find_channel(channel_name, server):
    return next(
        channel for channel in server.channels if channel.name == channel_name or str(channel.id) == str(channel_name))


def embed_to_text(embed):
    text = ''
    if embed.title:
        text += '**' + embed.title + '**\n'
    if embed.description:
        text += embed.description + '\n'
    text += '\n'.join([f'{field.name}: {field.value}\n' for field in embed.fields])
    return text


def time_delta_to_parts(delta):
    days = delta.days
    hours, remainder = divmod(delta.seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    return {'day': days, 'hour': hours, 'minute': minutes, 'second': seconds}


def round_time_dict_to_minutes(time_dict):
    time_dict['minute'] += round(time_dict['second'] / 60)
    if time_dict['minute'] >= 60:
        time_dict['minute'] -= 60
        time_dict['hour'] += 1
    if time_dict['hour'] >= 24:
        time_dict['hour'] -= 24
        time_dict['day'] += 1
    return time_dict


# This is super oversimplified, but it works for my extremely limited purposes
def grammatical_number(word, count):
    if count == 1 or count == -1:
        return word
    return word + 's'

def run_only_one(func):
    if 'threads' not in run_only_one.__dict__:
        run_only_one.threads = {}
    def inner1(*args, **kwargs):
        thread = None
        if func in run_only_one.threads:
            thread = run_only_one.threads[func]
        if not thread or thread.done():
            run_only_one.threads[func] = asyncio.get_event_loop().create_task(func(*args, **kwargs))

    return inner1