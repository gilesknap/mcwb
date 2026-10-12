"""Exposed API functions."""

import re

import numpy as np
from mcipc.rcon.client import Client
from mcipc.rcon.enumerations import FillMode

from mcwb.functions import get_direction, normalize, offsets, validate
from mcwb.item import MINECRAFT_VERSION, Item
from mcwb.polygon import poly_profile
from mcwb.types import Anchor, Direction, Profile, Vec3

__all__ = ["make_tunnel"]


def make_tunnel(
    client: Client,
    profile: Profile | np.ndarray,
    start: Vec3,
    *,
    end: Vec3 | None = None,
    direction: Vec3 = Direction.UP,
    length: int = 1,
    anchor: Anchor = Anchor.CENTER,
    default: Item = Item.AIR,
    mode: FillMode = FillMode.KEEP,
    filter: str | None = None,
):
    """Creates a tunnel with the given profile."""

    start = Vec3(*start)  # Ensure Vec3 object.

    if validate(profile) != 2:
        raise ValueError("Invalid matrix.")

    if end is None:
        end = start + direction * (length - 1)
    else:
        end = Vec3(*end)  # Ensure Vec3 object.

    direction = direction or get_direction(start, end)
    profile = list(normalize(profile, default=default))

    for block, offset in offsets(profile, direction, anchor):
        client.fill(start + offset, end + offset, block, mode=mode, filter=filter)  # type: ignore


def polygon(
    client: Client,
    center: Vec3,
    height: int,
    diameter: int,
    sides=4,
    direction=Direction.UP,
    item: Item = Item.STONE,
    offset=None,
    mode=FillMode.KEEP,
    fill_item: Item = Item.AIR,
):
    """
    Place a polygon in the world

    TODO - lots of arguments here - maybe should use classes for the API instead?
    Tunnel, Polygon ...
    """

    profile = poly_profile(
        sides=sides, diameter=diameter, item=item, offset=offset, fill_item=fill_item
    )
    make_tunnel(client, profile, center, length=height, direction=direction, mode=mode)


# loot spawn drops its items here: far enough below the bottom of any vanilla
# dimension (the overworld starts at y=-64) that the server discards them on
# the next tick instead of letting them pile up on the bedrock floor
_dump_y = -1000
_extract_item = re.compile(r".*minecraft\:(?:blocks\/)?(.+)$")
# blocks with no loot table (air, water, bedrock, ...) make loot fail with this
# message, which contains the English display name of the block
_no_loot_table = re.compile(r"^Block (.+) has no loot table$")
# display names that do not convert to the block id by the default rule
_display_name_ids = {"jigsaw_block": "jigsaw"}


def _block_id_from_display_name(display_name: str) -> str:
    block_id = display_name.lower().replace(" ", "_")
    return _display_name_ids.get(block_id, block_id)


def get_block(client: Client, pos: Vec3) -> Item:
    """Get the block at the given position.

    Uses ``loot spawn <dump> mine <pos>``, which reports the loot table of the
    block, i.e. ``minecraft:blocks/<id>``. Blocks without a loot table such as
    air, water or bedrock are identified from the error message instead.

    Some blocks share the loot table of a related block, e.g. a wall torch
    reads back as a torch and a wall sign as a sign.

    Raises ValueError if the position is not loaded or the server reports a
    block identifier that is not in `Item` (i.e. one added after
    ``MINECRAFT_VERSION``).
    """

    # loot.spawn creates an item entity - drop it into the void below pos so
    # that it is discarded and does not need a separate loaded chunk
    dump = (pos.x, _dump_y, pos.z)

    output = client.loot.spawn(dump).mine(pos)  # type: ignore
    if match := _no_loot_table.search(output):
        name = _block_id_from_display_name(match.group(1))
    elif match := _extract_item.search(output):
        name = match.group(1)
    else:
        raise ValueError(f"unexpected response from loot spawn: {output}")
    if name == "empty":
        name = "air"

    try:
        return Item(name)
    except ValueError as e:
        raise ValueError(
            f"unknown block '{name}': mcwb.Item is generated from Minecraft "
            f"{MINECRAFT_VERSION}, regenerate it with scripts/generate_items.py"
        ) from e
