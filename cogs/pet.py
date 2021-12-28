import datetime
import random
import sys

from discord import slash_command, Option, Interaction, Embed, Cog, Member, ButtonStyle
from discord.ui import View, button, Button

import generator
import utils
from botdb import BotDB
import botconfig as conf
from views.confirm import Confirm

tick = datetime.timedelta(minutes=120)

maxFood = 30
maxHappy = 30

foodGain = 6
happyGain = 6

dbname = 'pets'
feedEmoji = u'\U0001F355'
petEmoji = u'\U0001F49C'


class PetView(View):
    def __init__(self, pet, owner):
        super().__init__(timeout=600)
        self.pet = pet
        self.owner = owner

    @button(
        label="Feed me!",
        style=ButtonStyle.blurple,
        emoji=feedEmoji
    )
    async def feed(self, _: Button, interaction: Interaction):
        message = self.pet.feed()
        embed = self.pet.render()
        embed.add_field(name='Result', value=message)
        await interaction.message.edit(embed=embed)
        save_pet(self.pet, self.owner)

    @button(
        label="Pet me!",
        style=ButtonStyle.green,
        emoji=petEmoji
    )
    async def pet(self, _: Button, interaction: Interaction):
        message = self.pet.pet()
        embed = self.pet.render()
        embed.add_field(name='result', value=message)
        await interaction.message.edit(embed=embed)
        save_pet(self.pet, self.owner)

    async def on_timeout(self):
        self.clear_items()
        embed = self.pet.render()
        embed.set_footer(text='Timed out. Use !pet to interact again.')
        await self.interaction.edit_original_message(view=self, embed=embed)


class Pet:
    def __init__(self):
        self.seed = None
        self.desc = None
        self.name = 'Familiar'
        self.food = 0
        self.happy = 0
        self.feedText = 'You offer the wizard\'s familiar a treat from your pocket. She takes it and retreats to her ' \
                        'perch. '
        self.fullText = 'You offer the wizard\'s familiar a treat from your pocket, but she seems full.'
        self.hungryPetText = 'You try to pet the wizard\'s familiar. She tries to bite your hand. Perhaps she\'s ' \
                             'hungry? '
        self.midPetText = 'You scratch the wizard\'s familiar under the chin. She chitters contentedly.'
        self.fullPetText = 'The wizard\'s familiar rubs against you, trilling happily.'
        self.lastCheck = datetime.datetime.now()

    def feed(self):
        self.update()
        if self.food < maxFood:
            self.food = min(maxFood, self.food + foodGain)
            message = self.feedText
        else:
            message = self.fullText

        return message

    def pet(self):
        self.update()
        factor = self.food / maxFood
        if factor < 0.3:
            message = self.hungryPetText
        elif factor < 0.75:
            message = self.midPetText
        else:
            message = self.fullPetText
        self.happy = min(maxHappy, int(self.happy + (happyGain * factor)))
        return message

    def render(self):
        embed = Embed()
        try:
            embed.title = self.name
            pet_description = generator.extract_text(self.desc['description'])
            embed.description = f"{pet_description} that can {generator.extract_text(self.desc['ability'])} "
        except AttributeError:
            embed.title = 'Familiar'
        embed.add_field(name='Fed', value=f'```\n{utils.draw_gauge(self.food, maxFood)}\n```', inline=False)
        embed.add_field(name='Happiness', value=f'```\n{utils.draw_gauge(self.happy, maxHappy)}\n```', inline=False)
        if '.hex' in self.desc['description']['beastColor']:
            embed.colour = self.desc['description']['beastColor']['.hex']
        if self.seed:
            embed.set_footer(text=f'seed: {self.seed}')
        return embed

    def update(self):
        temp = self.lastCheck + tick
        if temp < datetime.datetime.now():
            self.lastCheck = datetime.datetime.now()
        while temp < datetime.datetime.now():
            temp += tick
            self.food = max(0, self.food - 1)
            self.happy = max(0, self.food - 1)

    def set_stats(self, name, desc, seed):
        self.name = name
        self.desc = desc
        self.feedText = f'you offer {name} a treat from your pocket. It seems to enjoy it.'
        self.fullText = f'you offer {name} a treat from your pocket, but it seems full.'
        self.hungryPetText = f'you try to pet {name}. It tries to bite your hand. Perhaps it\'s hungry?'
        self.midPetText = f'you scratch {name} under the chin. It looks at you contentedly.'
        self.fullPetText = f"{name} rubs against you, {desc['description']['species']['sound']['text']} happily."
        self.seed = seed


def load_pet(name):
    with BotDB(conf.bot_name(), dbname) as db:
        my_pet = db[name]
    my_pet.update()
    return my_pet


def save_pet(my_pet, name):
    with BotDB(conf.bot_name(), dbname) as db:
        db[name] = my_pet


def summoner(seed):
    if not seed:
        seed = str(random.randrange(sys.maxsize))

    async def summon_callback(interaction):
        user_id = str(interaction.user.id)

        my_pet = Pet()
        summon = generator.generate('beast', seed)
        my_pet.set_stats(generator.generate('mc.name', seed)['text'], summon['core'], seed)
        message = generator.extract_text(summon) + f' Its name is {my_pet.name}.'
        save_pet(my_pet, user_id)
        await interaction.response.edit_message(content="Summoning...", embed=None, view=None)
        await interaction.followup.send(message)

    return summon_callback


class PetCommands(Cog):
    def __init__(self, bot):
        self.bot = bot

    @slash_command(name='summon', description='Summon a new pet!')
    async def summon(self, ctx, seed: str = None):
        confirm_view = Confirm(summoner(seed))
        try:
            my_pet = load_pet(str(ctx.user.id))
            message = 'This will replace your existing pet, shown below. Are you sure?'
            embed = my_pet.render()
            await ctx.respond(message, view=confirm_view, embed=embed, ephemeral=True)
        except KeyError:
            message = "You don't have a pet yet! Are you ready to summon one?"
            await ctx.respond(message, view=confirm_view, ephemeral=True)

    @slash_command(name='pet', description='View and care for a pet!')
    async def view(self,
                   ctx,
                   target: Option(Member, 'Whose pet?', required=False)
                   ):
        owner = ctx.user
        if target is not None:
            owner = target
        try:
            my_pet = load_pet(str(owner.id))
        except KeyError:
            if owner == ctx.user:
                await ctx.respond("Failed to load your pet. Maybe you don't have one? Try `/summon` to get one now!",
                                  ephemeral=True)
            else:
                await ctx.respond(
                    f"Failed to load {owner.display_name}'s pet. Maybe they don't have one? They should try /summon!",
                    ephemeral=True)
            return
        embed = my_pet.render()
        view = PetView(my_pet, str(owner.id))
        view.interaction = await ctx.respond(f'{owner.mention}\'s pet!', view=view, embed=embed)
