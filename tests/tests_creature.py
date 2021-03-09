import unittest

from tests.tests_tibiapy import TestCommons
from tibiapy import BoostedCreature, InvalidContent, CreaturesSection, CreatureDetail

FILE_CREATURE_SECTION = "library/creature_list.txt"
FILE_CREATURE = "library/creature_animatedfeather.txt"

class TestCreature(TestCommons, unittest.TestCase):
    # region Tibia.com Tests
    def test_creature_from_content(self):
        """Testing parsing a boosted creature"""
        content = self.load_resource(self.FILE_UNRELATED_SECTION)
        creature = BoostedCreature.from_content(content)

        self.assertIsInstance(creature, BoostedCreature)
        self.assertEqual("Skeleton Warrior", creature.name)

    def test_creature_from_content_not_tibiacom(self):
        """Testing parsing a page that is not Tibia.com"""
        with self.assertRaises(InvalidContent):
            BoostedCreature.from_content("<html><div><p>Nothing</p></div></html>")

    def test_creature_section_from_content(self):
        content = self.load_resource(FILE_CREATURE_SECTION)
        creatures = CreaturesSection.from_content(content)

        self.assertIsNotNone(creatures)
        self.assertIsNotNone(creatures.boosted_creature)
        self.assertEqual("Blood Crab", creatures.boosted_creature.name)
        self.assertEqual("bloodcrab", creatures.boosted_creature.race)
        self.assertIsNotNone(creatures.boosted_creature.image_url)
        self.assertIsNotNone(creatures.boosted_creature.url)
        self.assertEqual(536, len(creatures.creatures))
        for creature in creatures.creatures:
            with self.subTest(name=creature.name):
                self.assertIsInstance(creature.name, str)
                self.assertIsInstance(creature.race, str)

    def test_creature_detail_from_content(self):
        content = self.load_resource(FILE_CREATURE)
        creature = CreatureDetail.from_content(content)

        self.assertIsNotNone(creature)
        self.assertEqual("Animated Feathers", creature.name)
        self.assertEqual("animatedfeather", creature.race)
        self.assertIsNotNone(creature.description)
    # endregion
