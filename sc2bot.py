import sc2
import random
from build import Build
from sc2 import run_game, maps, Race, Difficulty
from sc2.player import Bot, Computer, Human
from sc2.ids.unit_typeid import UnitTypeId
from sc2.ids.ability_id import AbilityId
from sc2.ids.upgrade_id import UpgradeId
from sc2.ids.buff_id import BuffId
from sc2.unit import Unit
from sc2.units import Units
from sc2.position import Point2
from sc2.ids.buff_id import BuffId

class XackaBot(sc2.BotAI):
	def __init__(self):
		self.BUILD = Build.MASS_MARINES
		if self.BUILD == Build.MASS_MARINES:
			self.MAX_WORKERS = 46
			self.CENTER_WORKERS = 22
			self.NUM_REFINERY = 0
			self.NUM_BARRACKS = 0
			self.NUM_BREACTOR = 0
			self.NUM_COMMANDCENTER = 1
			self.NUM_RESEARCHBAY = 0

	async def on_step(self, iteration):
		self.iteration = iteration
		await self.distribute_workers()
		await self.build_workers()
		await self.build_supply()
		await self.build_refinery()
		await self.build_barracks()
		await self.build_barrack_reactors()
		await self.build_bay()
		await self.bay_research()
		await self.build_troops()
		await self.attack()
		await self.expand()
		await self.check_build()

	async def build_workers(self):
		if (self.structures(UnitTypeId.COMMANDCENTER).amount * self.CENTER_WORKERS > self.units(UnitTypeId.SCV).amount and self.units(UnitTypeId.SCV).amount < self.MAX_WORKERS and self.supply_left >= 1):
			for center in self.structures(UnitTypeId.COMMANDCENTER).idle:
				if (self.can_afford(UnitTypeId.SCV)):
					center.train(UnitTypeId.SCV)

	async def build_supply(self):
		if not self.already_pending(UnitTypeId.SUPPLYDEPOT) and self.supply_left < 5 and self.can_afford(UnitTypeId.SUPPLYDEPOT):
			workers = self.workers.gathering
			if workers:
				worker = workers.furthest_to(workers.center)
				location = await self.find_placement(UnitTypeId.SUPPLYDEPOT, worker.position, placement_step = 3)
				if location:
					worker.build(UnitTypeId.SUPPLYDEPOT, location)
		for depot in self.structures(UnitTypeId.SUPPLYDEPOT).ready:
			depot(AbilityId.MORPH_SUPPLYDEPOT_LOWER)

	async def build_refinery(self):
		if(not self.already_pending(UnitTypeId.REFINERY) and self.structures(UnitTypeId.REFINERY).amount < self.NUM_REFINERY):
			for center in self.structures(UnitTypeId.COMMANDCENTER).ready:
				vaspenes = self.vespene_geyser.closer_than(15, center)
				for vaspene in vaspenes:
					worker = self.select_build_worker(vaspene.position)
					if (not self.can_afford(UnitTypeId.REFINERY) or worker is None):
						break
					if (not self.structures(UnitTypeId.REFINERY).closer_than(1.0, vaspene).exists):
						worker.build(UnitTypeId.REFINERY, vaspene)

	async def expand(self):
		if (not self.already_pending(UnitTypeId.COMMANDCENTER) and self.can_afford(UnitTypeId.COMMANDCENTER) and self.structures(UnitTypeId.COMMANDCENTER).amount < self.NUM_COMMANDCENTER):
			await self.expand_now()

	async def build_barracks(self):
		if (not self.already_pending(UnitTypeId.BARRACKS) and self.can_afford(UnitTypeId.BARRACKS) and self.structures(UnitTypeId.BARRACKS).amount < self.NUM_BARRACKS):
			workers = self.workers.gathering
			if workers:
				worker = workers.furthest_to(workers.center)
				location = await self.find_placement(UnitTypeId.BARRACKS, self.townhalls.random.position, addon_place = True, placement_step = 5)
				if location:
					worker.build(UnitTypeId.BARRACKS, location)

	async def build_barrack_reactors(self):
		if(not self.already_pending(UnitTypeId.BARRACKSREACTOR) and self.structures(UnitTypeId.BARRACKSREACTOR).amount < self.NUM_BREACTOR):
			for barrack in self.structures(UnitTypeId.BARRACKS).idle:
				if (self.can_afford(UnitTypeId.BARRACKSREACTOR) and not barrack.has_add_on):
					barrack.build(UnitTypeId.BARRACKSREACTOR)

	async def build_troops(self):
		for barrack_r in self.structures(UnitTypeId.BARRACKSREACTOR):
			if (self.can_afford(UnitTypeId.MARINE) and self.supply_left >= 2 and len(barrack_r.orders) < 2):
				barrack_r.train(UnitTypeId.MARINE)
		for barrack in self.structures(UnitTypeId.BARRACKS).idle:
			if (self.can_afford(UnitTypeId.MARINE) and self.supply_left >= 1):
				barrack.train(UnitTypeId.MARINE)

	async def build_bay(self):
		if (not self.already_pending(UnitTypeId.ENGINEERINGBAY) and self.can_afford(UnitTypeId.ENGINEERINGBAY) and self.structures(UnitTypeId.ENGINEERINGBAY).amount < self.NUM_RESEARCHBAY):
			workers = self.workers.gathering
			if workers:
				worker = workers.furthest_to(workers.center)
				location = await self.find_placement(UnitTypeId.ENGINEERINGBAY, self.townhalls.random.position, placement_step = 5)
			if location:
				worker.build(UnitTypeId.ENGINEERINGBAY, location)

	async def bay_research(self):
		for bay in self.structures(UnitTypeId.ENGINEERINGBAY).idle:
			if (self.can_afford(UpgradeId.TERRANINFANTRYWEAPONSLEVEL1)):
				bay.research(UpgradeId.TERRANINFANTRYWEAPONSLEVEL1)

	async def check_build(self):
		if self.units(UnitTypeId.SCV).amount == 16:
			self.NUM_COMMANDCENTER = 2
		elif self.structures(UnitTypeId.COMMANDCENTER).amount == 2:
			self.NUM_BARRACKS = 1

	async def attack(self):
		if (self.units(UnitTypeId.MARINE).amount > 20):
			for marine in self.units(UnitTypeId.MARINE).idle:
				marine.attack(self.find_target(self.state))

	def find_target(self, state):
		target_units = self.enemy_units.filter(lambda unit: unit.can_be_attacked)
		if (len(target_units) > 0):
			return random.choice(target_units)
		target_structures = self.enemy_structures.filter(lambda unit: unit.can_be_attacked)
		if (len(target_structures) > 0):
			return random.choice(target_structures)
		else:
			return self.enemy_start_locations[0]

run_game(maps.get("Abyssal Reef LE"), [
	Bot(Race.Terran, XackaBot(), fullscreen = False),
	Computer(Race.Terran, Difficulty.Medium)
], realtime = True)
