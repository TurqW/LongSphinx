from discord import Embed

import botconfig as conf


class DefaultEmbed(Embed):
    def __init__(self, server, **kwargs):
        super().__init__(**kwargs)
        self.color = conf.get_object(server, 'embedColor')
        # There may be other defaults I want to set later, idk
