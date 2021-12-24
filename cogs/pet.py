import datetime
import discord
import random
import sys
from discord.commands import Option, slash_command

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
class PetView(discord.ui.View):
	def __init__(self, pet, owner):
		super().__init__(timeout=600)
		self.pet = pet
		self.owner = owner

	@discord.ui.button(
		label="Feed me!",
		style=discord.ButtonStyle.blurple,
		emoji=feedEmoji
	)
	async def feed(self, button: discord.ui.Button, interaction: discord.Interaction):
		message = self.pet.feed()
		embed = self.pet.render()
		embed.add_field(name='result', value=message)
		await interaction.message.edit(embed=embed)
		savePet(self.pet, self.owner)

	@discord.ui.button(
		label="Pet me!",
		style=discord.ButtonStyle.green,
		emoji=petEmoji
	)
	async def pet(self, button: discord.ui.Button, interaction: discord.Interaction):
		message = self.pet.pet()
		embed = self.pet.render()
		embed.add_field(name='result', value=message)
		await interaction.message.edit(embed=embed)
		savePet(self.pet, self.owner)

	async def on_timeout(self):
		self.clear_items()
		embed = self.pet.render()
		embed.set_footer(text='Timed out. Use !pet to interact again.')
		await self.interaction.edit_original_message(view=self, embed=embed)

class Pet:
	def __init__(self):
		self.food = 0
		self.happy = 0
		self.feedText = 'You offer the wizard\'s familiar a treat from your pocket. She takes it and retreats to her perch.'
		self.fullText = 'You offer the wizard\'s familiar a treat from your pocket, but she seems full.'
		self.hungryPetText = 'You try to pet the wizard\'s familiar. She tries to bite your hand. Perhaps she\'s hungry?'
		self.midPetText = 'You scratch the wizard\'s familiar under the chin. She chitters contentedly.'
		self.fullPetText = 'The wizard\'s familiar rubs against you, trilling happily.'
		self.lastCheck = datetime.datetime.now()

	def feed(self):
		self.update()
		message = ''
		if (self.food < maxFood):
			self.food = min(maxFood, self.food + foodGain)
			message = self.feedText
		else:
			message = self.fullText

		return message

	def pet(self):
		self.update()
		factor = self.food/maxFood
		message = ''
		if factor < 0.3:
			message = self.hungryPetText
		elif factor < 0.75:
			message = self.midPetText
		else:
			message = self.fullPetText
		self.happy = min(maxHappy, int(self.happy + (happyGain * factor)))
		return message


	def render(self):
		embed = discord.Embed()
		try:
			embed.title = self.name
			embed.description = f"{generator.extract_text(self.desc['description'])} that can {generator.extract_text(self.desc['ability'])}"
		except AttributeError:
			embed.title = 'Familiar'
		embed.add_field(name='Fed', value='```\n' + utils.drawGauge(self.food, maxFood) + '\n```', inline=False)
		embed.add_field(name='Happiness', value='```\n' + utils.drawGauge(self.happy, maxHappy) + '\n```', inline=False)
		if '.hex' in self.desc['description']['beastColor']:
			embed.color = self.desc['description']['beastColor']['.hex']
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

	def setStats(self, name, desc, seed):
		self.name = name
		self.desc = desc
		self.feedText = f'you offer {name} a treat from your pocket. It seems to enjoy it.'
		self.fullText = f'you offer {name} a treat from your pocket, but it seems full.'
		self.hungryPetText = f'you try to pet {name}. It tries to bite your hand. Perhaps it\'s hungry?'
		self.midPetText = f'you scratch {name} under the chin. It looks at you contentedly.'
		self.fullPetText = f"{name} rubs against you, {desc['description']['species']['sound']['text']} happily."
		self.seed = seed

def loadPet(name):
	with BotDB(conf.bot_name(), dbname) as db:
		myPet = db[name]
	myPet.update()
	return myPet

def savePet(myPet, name):
	with BotDB(conf.bot_name(), dbname) as db:
		db[name] = myPet

class PetCommands(discord.Cog):
	def __init__(self, bot):
		self.bot = bot

	@slash_command(name='summon', description='Summon a new pet!', guild_ids=[489197880809095168])
	async def summon(self, ctx, seed: str = None):
		confirmer = Confirm(self.summoner(seed), Confirm.cancel_action )
		try:
			myPet = loadPet(str(ctx.user.id))
			message = 'This will replace your existing pet, shown below. Are you sure?'
			embed = myPet.render()
			await ctx.respond(message, view=confirmer, embed=embed, ephemeral=True)
		except:
			message = "You don't have a pet yet! Are you ready to summon one?"
			await ctx.respond(message, view=confirmer, ephemeral=True)
		

	def summoner(self, seed):
		if not seed:
				seed = str(random.randrange(sys.maxsize))

		async def summon_callback(interaction):
			id = str(interaction.user.id)
			
			myPet = Pet()
			summon = generator.generate('beast', seed)
			myPet.setStats(generator.generate('mc.name', seed)['text'], summon['core'], seed)
			message = generator.extract_text(summon) + f' Its name is {myPet.name}.'
			savePet(myPet, id)
			await interaction.response.edit_message(content="Summoning...", embed=None, view=None)
			await interaction.followup.send(message)

		return summon_callback

	@slash_command(name='pet', description='View and care for a pet!', guild_ids=[489197880809095168])
	async def view(self, ctx, target:  Option(str, "Whose pet do you want to view?", autocomplete=utils.user_picker, required=False) = None):
		owner = ctx.user
		if target is not None:
			owner = ctx.guild.get_member_named(target)
		try:
			myPet = loadPet(str(owner.id))
		except:
			if owner == ctx.user:
				await ctx.respond("Failed to load your pet. Maybe you don't have one? Try `/summon` to get one now!", ephemeral=True)
			else:
				await ctx.respond(f"Failed to load {owner.display_name}'s pet. Maybe they don't have one? They should try /summon !", ephemeral=True)
			return
		embed = myPet.render()
		view = PetView(myPet, str(owner.id))
		view.interaction = await ctx.respond(f'{owner.mention}\'s pet!', view=view, embed=embed)

def readme(**kwargs):
	return """Pets:
* `!summon` generate a new random pet for you! **Warning: will delete your old pet if you have one.**
* `!pet` view your pet. @mention someone else to view their pet instead. Use the reactions to feed and pet them.
* `!getseed` find the seed for your pet. If you save this somewhere, you can `!summon <seed>` to get back to this pet if something happens.
"""
