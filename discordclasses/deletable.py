from typing import Callable, List, Coroutine

from discord import ButtonStyle, Interaction, Button, SelectOption
from discord.ui import button, View, Select


async def just_defer(interaction):
    await interaction.response.defer()


class DeletableListView(View):
    def __init__(self,
                 message_refresher: Callable[[Interaction, View], Coroutine],
                 dropdown_populator: Callable[[Interaction], List[SelectOption]],
                 item_deleter: Callable[[List], None]
                 ):
        super().__init__()
        self.dropdown = None
        self.message_refresher = message_refresher
        self.dropdown_populator = dropdown_populator
        self.item_deleter = item_deleter

    @button(label="Delete some?", row=2, style=ButtonStyle.grey, emoji='🗑️')
    async def delete(self, this_button: Button, interaction: Interaction):
        if not self.dropdown:
            options = self.dropdown_populator(interaction)

            self.dropdown = Select(
                placeholder="Delete which one(s)?",
                max_values=len(options),
                options=options
            )
            self.dropdown.callback = just_defer
            self.add_item(self.dropdown)

            this_button.label = 'Delete'
            this_button.style = ButtonStyle.red
            view = self
        else:
            self.item_deleter(self.dropdown.values)
            view = DeletableListView(self.message_refresher, self.dropdown_populator, self.item_deleter)
        await self.message_refresher(interaction, view)
