from typing import Callable

import discord


async def cancel_action(interaction: discord.Interaction):
    await interaction.response.edit_message(content='Action cancelled.', embed=None, view=None)


class Confirm(discord.ui.View):
    def __init__(self,
                 confirm_callback: Callable,
                 middle_callback: Callable = None,
                 cancel_callback: Callable = cancel_action,
                 confirm_label: str = 'Confirm',
                 middle_label: str = None,
                 cancel_label: str = 'Cancel'):
        super().__init__()
        self.confirm_callback = confirm_callback
        self.cancel_callback = cancel_callback
        if not (middle_callback and middle_label):
            self.remove_item(self.middle)
        else:
            self.middle_callback = middle_callback
            self.middle.label = middle_label
        self.confirm.label = confirm_label
        self.cancel.label = cancel_label

    @discord.ui.button(style=discord.ButtonStyle.green)
    async def confirm(self, _: discord.ui.Button, interaction: discord.Interaction):
        await self.confirm_callback(interaction)

    @discord.ui.button(style=discord.ButtonStyle.grey)
    async def middle(self, _: discord.ui.Button, interaction: discord.Interaction):
        await self.middle_callback(interaction)

    @discord.ui.button(style=discord.ButtonStyle.red)
    async def cancel(self, _: discord.ui.Button, interaction: discord.Interaction):
        await self.cancel_callback(interaction)
