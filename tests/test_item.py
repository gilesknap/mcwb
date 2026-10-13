"""Tests for the generated mcwb.item.Item enum and its integration."""

import json

import pytest
from mcipc.rcon.enumerations import Item as McipcItem

from mcwb import MINECRAFT_VERSION, Direction, Item, Vec3, get_block
from mcwb.itemlists import load_items, save_items
from tests.mockclient import MockClient


@pytest.mark.parametrize(
    "name",
    ["deepslate", "cherry_planks", "mangrove_log", "pale_oak_log", "resin_block"],
)
def test_modern_blocks(name: str):
    assert Item(name) == f"minecraft:{name}"
    assert Item(f"minecraft:{name}") is Item(name)


def test_mcipc_compatibility():
    # members are interchangeable with mcipc's enum and plain strings
    assert Item.STONE == McipcItem.STONE
    assert hash(Item.STONE) == hash(McipcItem.STONE)  # usable as dict keys
    assert Item.STONE == "minecraft:stone"
    assert str(Item.STONE) == "minecraft:stone"


def test_minecraft_version():
    assert MINECRAFT_VERSION


def test_unknown_item():
    with pytest.raises(ValueError):
        Item("not_a_real_block")


def test_get_block_modern():
    client = MockClient()
    pos = Vec3(1, 2, 3)
    client.setblock(pos, Item.DEEPSLATE)
    assert get_block(client, pos) is Item.DEEPSLATE  # type: ignore


class _LootClient:
    """Return a canned response to ``loot spawn ... mine ...``."""

    def __init__(self, response: str):
        self.response = response

    @property
    def loot(self):
        response = self.response

        class Spawn:
            def spawn(self, dump):
                assert dump[1] < -128  # below the void kill level

                class Mine:
                    def mine(self, pos):
                        return response

                return Mine()

        return Spawn()


@pytest.mark.parametrize(
    "response, expected",
    [
        # real responses from a Minecraft 26.3 server
        (
            "Dropped 1 [Dirt] from loot table minecraft:blocks/grass_block",
            Item.GRASS_BLOCK,
        ),
        ("Dropped 0 items from loot table minecraft:blocks/glass", Item.GLASS),
        ("Dropped 0 items from loot table minecraft:empty", Item.AIR),
        ("Block Air has no loot table", Item.AIR),
        ("Block Cave Air has no loot table", Item.CAVE_AIR),
        ("Block Water has no loot table", Item.WATER),
        ("Block Bedrock has no loot table", Item.BEDROCK),
        ("Block Jigsaw Block has no loot table", Item.JIGSAW),
    ],
)
def test_get_block_responses(response, expected):
    client = _LootClient(response)
    assert get_block(client, Vec3(0, 0, 0)) is expected  # type: ignore


def test_get_block_not_loaded():
    client = _LootClient("That position is not loaded")
    with pytest.raises(ValueError, match="unexpected response"):
        get_block(client, Vec3(0, 0, 0))  # type: ignore


def test_direction_methods():
    # classmethod properties were removed in Python 3.13, these are methods now
    assert Direction.cardinals() == [
        Direction.SOUTH,
        Direction.WEST,
        Direction.NORTH,
        Direction.EAST,
    ]
    assert len(Direction.all()) == 6
    assert Direction.values()[4] == Direction.UP
    assert Direction.name(Direction.NORTH) == "north"


def test_save_load_round_trip(tmp_path):
    row = [Item.DEEPSLATE, Item.AIR, Item.CHERRY_PLANKS]
    path = tmp_path / "row.json"
    save_items(row, path)
    assert json.loads(path.read_text())[0] == {"__Item__": "minecraft:deepslate"}
    loaded = load_items(path, 1)
    assert loaded == row
    assert all(isinstance(item, Item) for item in loaded)  # type: ignore


def test_load_bare_strings(tmp_path):
    path = tmp_path / "row.json"
    path.write_text('["minecraft:stone", "air"]')
    assert load_items(path, 1) == [Item.STONE, Item.AIR]
