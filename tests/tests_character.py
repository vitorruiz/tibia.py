import datetime

import tests.tests_guild
from tests.tests_tibiapy import TestTibiaPy
from tibiapy import Character, Death, InvalidContent, Killer
from tibiapy.enums import AccountStatus, Sex, Vocation
from tibiapy.utils import parse_tibia_datetime

FILE_CHARACTER_RESOURCE = "character/tibiacom_full.txt"
FILE_CHARACTER_NOT_FOUND = "character/tibiacom_not_found.txt"
FILE_CHARACTER_FORMER_NAMES = "character/tibiacom_former_names.txt"
FILE_CHARACTER_DELETION = "character/tibiacom_deletion.txt"
FILE_CHARACTER_DEATHS_COMPLEX = "character/tibiacom_deaths_complex.txt"

FILE_CHARACTER_TIBIADATA = "character/tibiadata.json"
FILE_CHARACTER_TIBIADATA_UNHIDDEN = "character/tibiadata_unhidden.json"
FILE_CHARACTER_TIBIADATA_DELETED = "character/tibiadata_deleted.json"
FILE_CHARACTER_TIBIADATA_NOT_FOUND = "character/tibiadata_not_found.json"


class TestCharacter(TestTibiaPy):
    def _compare_character(self, mock_character, character):
        self.assertEqual(mock_character.name, character.name)
        self.assertEqual(mock_character.world, character.world)
        self.assertEqual(mock_character.vocation, character.vocation)
        self.assertEqual(mock_character.level, character.level)
        self.assertEqual(mock_character.sex, character.sex)

    def testCharacter(self):
        character = Character.from_content(self._load_resource(FILE_CHARACTER_RESOURCE))
        self._compare_character(Character("Tschas", "Gladera", Vocation.DRUID, 205, Sex.FEMALE), character)
        self.assertIsNotNone(character.guild_membership)
        self.assertEqual("Redd Alliance", character.guild_membership.name)
        self.assertEqual("Mentor", character.guild_membership.rank)
        self.assertIsNotNone(character.guild_url)
        self.assertIsNone(character.married_to_url)
        self.assertEqual(character.guild_name, character.guild_membership.name)
        self.assertEqual(character.guild_rank, character.guild_membership.rank)
        self.assertEqual(AccountStatus.FREE_ACCOUNT, character.account_status)
        self.assertEqual(139, character.achievement_points)
        self.assertIsNone(character.house)
        self.assertIsNone(character.deletion_date)
        self.assertIsNotNone(character.deaths)
        self.assertEqual(0, character.deaths.__len__())
        self.assertEqual(parse_tibia_datetime("Apr 22 2018, 16:00:38 CEST"), character.last_login)
        self.assertEqual(character.url, Character.get_url(character.name))

    def testCharacterNotFound(self):
        content = self._load_resource(FILE_CHARACTER_NOT_FOUND)
        char = Character.from_content(content)
        self.assertIsNone(char)

    def testCharacterFormerNames(self):
        content = self._load_resource(FILE_CHARACTER_FORMER_NAMES)
        char = Character.from_content(content)
        self.assertIsInstance(char.former_names, list)
        self.assertTrue(char.former_names)
        self.assertEqual(len(char.former_names), 2)

    def testCharacterDeletion(self):
        content = self._load_resource(FILE_CHARACTER_DELETION)
        char = Character.from_content(content)
        self.assertEqual("Expendable Dummy", char.name)
        self.assertIsNotNone(char.deletion_date)
        self.assertIsInstance(char.deletion_date, datetime.datetime)
        self.assertEqual(parse_tibia_datetime("Oct 08 2018 22:17:00 CEST"), char.deletion_date)

    def testCharacterComplexDeaths(self):
        content = self._load_resource(FILE_CHARACTER_DEATHS_COMPLEX)
        char = Character.from_content(content)
        self.assertTrue(char.deaths)
        self.assertIsInstance(char.deaths[0], Death)
        self.assertEqual(len(char.deaths), 19)
        oldest_death = char.deaths[-1]
        self.assertEqual(oldest_death.killer.summon, "a fire elemental")

    def testCharacterUnrelated(self):
        content = self._load_resource(self.FILE_UNRELATED_SECTION)
        with self.assertRaises(InvalidContent):
            Character.from_content(content)

    def testDeathTypes(self):
        assisted_suicide = Death("Galarzaa", 280, killers=[Killer("Galarzaa", True), Killer("a pixy")],
                                 time=datetime.datetime.now())
        self.assertEqual(assisted_suicide.killer, assisted_suicide.killers[0])
        self.assertFalse(assisted_suicide.by_player)

        spawn_invasion = Death("Galarza", 270, killers=[Killer("a demon"), Killer("Nezune", True)])
        self.assertEqual(spawn_invasion.killer, spawn_invasion.killers[0])
        self.assertIsNone(spawn_invasion.killer.url)
        self.assertTrue(spawn_invasion.by_player)
        
    def testCharacterTibiaData(self):
        content = self._load_resource(FILE_CHARACTER_TIBIADATA)
        char = Character.from_tibiadata(content)

        self.assertEqual(char.url_tibiadata, Character.get_url_tibiadata(char.name))
        self.assertIsInstance(char, Character)
        self.assertIsNotNone(char.guild_name)
        self.assertIsInstance(char.last_login, datetime.datetime)

        self.assertTrue(char.deaths[3].by_player)

    def testCharacterTibiaDataUnhidden(self):
        content = self._load_resource(FILE_CHARACTER_TIBIADATA_UNHIDDEN)
        char = Character.from_tibiadata(content)

        self.assertIsNotNone(char.account_information)
        self.assertTrue(char.other_characters)
        self.assertFalse(char.hidden)

    def testCharacterTibiaDataDeleted(self):
        content = self._load_resource(FILE_CHARACTER_TIBIADATA_DELETED)
        char = Character.from_tibiadata(content)

        self.assertEqual(char.url_tibiadata, Character.get_url_tibiadata(char.name))
        self.assertIsInstance(char, Character)
        self.assertTrue(char.deleted)
        self.assertIsInstance(char.deletion_date, datetime.datetime)
        self.assertIsNone(char.guild_name)
        self.assertIsNone(char.last_login)

    def testCharacterTibiaDataNotFound(self):
        content = self._load_resource(FILE_CHARACTER_TIBIADATA_NOT_FOUND)
        char = Character.from_tibiadata(content)
        self.assertIsNone(char)

    def testCharacterTibiaDataInvalidJson(self):
        with self.assertRaises(InvalidContent):
            Character.from_tibiadata("<html><b>Not a json string</b></html>")

    def testCharacterTibiaDataUnrelatedJson(self):
        with self.assertRaises(InvalidContent):
            Character.from_tibiadata(self._load_resource(tests.tests_guild.FILE_GUILD_TIBIADATA))
