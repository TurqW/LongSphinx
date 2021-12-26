import discord
from typing import Callable


async def cancel_action(interaction: discord.Interaction):
    await interaction.response.edit_message(content='Action cancelled.', embed=None, view=None)


class Confirm(discord.ui.View):
    def __init__(self, confirm_callback: Callable, cancel_callback: Callable = cancel_action):
        super().__init__()
        self.confirm_callback = confirm_callback
        self.cancel_callback = cancel_callback

    @discord.ui.button(label="Confirm", style=discord.ButtonStyle.green)
    async def confirm(
            self, _: discord.ui.Button, interaction: discord.Interaction
    ):
        await self.confirm_callback(interaction)

    @discord.ui.button(label="Cancel", style=discord.ButtonStyle.red)
    async def cancel(self, _: discord.ui.Button, interaction: discord.Interaction):
        await self.cancel_callback(interaction)
