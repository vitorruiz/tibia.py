import datetime

from tests.tests_tibiapy import TestCommons
from tibiapy.exevo import auction_to_exevo, build_response, dump_snapshot, filter_auctions, last_server_save, \
    load_snapshot
from tibiapy.parsers import AuctionParser, CharacterBazaarParser

FILE_BAZAAR_CURRENT = "characterBazaar/bazaarCurrentAuctions.txt"
FILE_AUCTION_FINISHED = "auction/auctionFinished.txt"
FILE_AUCTION_UPGRADED_ITEMS = "auction/auctionWithUpgradedItems.txt"

UTC = datetime.timezone.utc


def make_auction(auction_id, **kwargs):
    auction = {
        "id": auction_id,
        "nickname": f"Char {auction_id}",
        "level": 100,
        "vocationId": 1,
        "auctionEnd": int(datetime.datetime(2100, 1, 1, tzinfo=UTC).timestamp()) + auction_id,
        "serverData": {
            "serverName": "Antica",
            "battleye": True,
            "pvpType": {"type": 1, "string": "Open PvP"},
            "serverLocation": {"type": 0, "string": "Europe"},
        },
        "skills": {"sword": 100.0, "magic": 10.0},
        "transfer": True,
    }
    auction.update(kwargs)
    return auction


class TestExevo(TestCommons):
    def test_auction_to_exevo_with_details(self):
        auction = AuctionParser.from_content(self.load_resource(FILE_AUCTION_FINISHED), 1)

        result = auction_to_exevo(auction)

        self.assertEqual(auction.auction_id, result["id"])
        self.assertEqual(auction.name, result["nickname"])
        self.assertEqual(auction.level, result["level"])
        self.assertEqual(auction.bid, result["currentBid"])
        self.assertTrue(result["detailed"])
        self.assertEqual(auction.details.charm_expansion, result["charmInfo"]["expansion"])
        self.assertEqual(auction.details.available_charm_points, result["charmInfo"]["unspent"])
        self.assertEqual(len(auction.details.charms), len(result["charms"]))
        self.assertEqual(set(result["skills"]), {"axe", "club", "distance", "fishing", "fist", "magic", "shielding",
                                                  "sword"})
        self.assertGreater(max(result["skills"].values()), 0)

    def test_auction_to_exevo_encodes_items_with_tier(self):
        auction = AuctionParser.from_content(self.load_resource(FILE_AUCTION_UPGRADED_ITEMS), 1)

        result = auction_to_exevo(auction)

        expected = [float(f"{i.item_id}.{i.tier}") for i in auction.displayed_items]
        self.assertEqual(expected, result["items"])

    def test_auction_to_exevo_without_details(self):
        bazaar = CharacterBazaarParser.from_content(self.load_resource(FILE_BAZAAR_CURRENT))

        result = auction_to_exevo(bazaar.entries[0], {"serverName": "Antica"})

        self.assertFalse(result["detailed"])
        self.assertEqual({"serverName": "Antica"}, result["serverData"])
        self.assertEqual([], result["charms"])
        self.assertFalse(result["transfer"])

    def test_snapshot_round_trip(self):
        snapshot = {"complete": True, "auctions": [make_auction(1)]}

        self.assertEqual(snapshot, load_snapshot(dump_snapshot(snapshot)))

    def test_last_server_save(self):
        # 10:00 CEST is 08:00 UTC in summer, 10:00 CET is 09:00 UTC in winter.
        summer_after = datetime.datetime(2025, 7, 10, 12, 0, tzinfo=UTC)
        summer_before = datetime.datetime(2025, 7, 10, 7, 0, tzinfo=UTC)
        winter_after = datetime.datetime(2025, 12, 10, 12, 0, tzinfo=UTC)

        self.assertEqual(datetime.datetime(2025, 7, 10, 8, 0, tzinfo=UTC), last_server_save(summer_after))
        self.assertEqual(datetime.datetime(2025, 7, 9, 8, 0, tzinfo=UTC), last_server_save(summer_before))
        self.assertEqual(datetime.datetime(2025, 12, 10, 9, 0, tzinfo=UTC), last_server_save(winter_after))

    def test_filter_auctions_excludes_ended_and_sorts_by_end(self):
        ended = make_auction(1, auctionEnd=100)
        auctions = [make_auction(3), ended, make_auction(2)]

        result = filter_auctions(auctions)

        self.assertEqual([2, 3], [a["id"] for a in result])

    def test_filter_auctions_by_server_vocation_and_level(self):
        auctions = [
            make_auction(1, level=50),
            make_auction(2, level=300, vocationId=4),
            make_auction(3, level=300, vocationId=1, serverData={
                "serverName": "Belobra", "battleye": False,
                "pvpType": {"type": 0}, "serverLocation": {"type": 1},
            }),
        ]

        self.assertEqual([2, 3], [a["id"] for a in filter_auctions(auctions, min_level=100)])
        self.assertEqual([2], [a["id"] for a in filter_auctions(auctions, vocation=[4])])
        self.assertEqual([3], [a["id"] for a in filter_auctions(auctions, server_set=["belobra"])])
        self.assertEqual([3], [a["id"] for a in filter_auctions(auctions, location=[1], pvp=[0])])
        self.assertEqual([3], [a["id"] for a in filter_auctions(auctions, battleye=[False])])
        self.assertEqual([1, 2], [a["id"] for a in filter_auctions(auctions, battleye=[True])])
        self.assertEqual([1], [a["id"] for a in filter_auctions(auctions, max_level=100)])

    def test_filter_auctions_by_skill(self):
        auctions = [make_auction(1), make_auction(2, skills={"sword": 80.0, "magic": 80.0})]

        self.assertEqual([1], [a["id"] for a in filter_auctions(auctions, skill_key=["sword"], min_skill=90)])
        self.assertEqual([1, 2], [a["id"] for a in filter_auctions(auctions, skill_key=["sword", "magic"],
                                                                   min_skill=80)])
        self.assertEqual([1, 2], [a["id"] for a in filter_auctions(auctions, skill_key=["sword"])])

    def test_filter_auctions_by_ids_and_nickname(self):
        auctions = [make_auction(1), make_auction(2), make_auction(3, nickname="Galarzaa Fidera")]

        self.assertEqual([2], [a["id"] for a in filter_auctions(auctions, auction_ids=[2])])
        self.assertEqual([3], [a["id"] for a in filter_auctions(auctions, nickname="fidera")])

    def test_build_response_paginates(self):
        results = [make_auction(i) for i in range(5)]

        first = build_response(results, 0, 2)
        last = build_response(results, 2, 2)

        self.assertEqual(2, len(first["page"]))
        self.assertTrue(first["hasNext"])
        self.assertFalse(first["hasPrev"])
        self.assertEqual(5, first["totalItems"])
        self.assertEqual(1, len(last["page"]))
        self.assertFalse(last["hasNext"])
        self.assertTrue(last["hasPrev"])
        self.assertEqual(5, last["endOffset"])
