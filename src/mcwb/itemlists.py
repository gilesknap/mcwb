"""
Functions for manipulating lists of Items
    1d = Row
    2d = Profile
    3d = Cuboid
"""

import json
from pathlib import Path
from typing import Any

import numpy as np
from mcipc.rcon.je import Client

from mcwb.api import get_block
from mcwb.functions import validate
from mcwb.item import Item
from mcwb.types import Cuboid, Items, Vec3
from mcwb.volume import Volume

ITEM_KEY = "__Item__"


def _to_json(items: Any) -> Any:
    """Recursively wrap each Item in a ``{"__Item__": id}`` object.

    This is done explicitly because ``Item`` is a ``str`` subclass, so the
    json module would otherwise write it as a bare string and never call a
    ``default`` hook.
    """
    if isinstance(items, list):
        return [_to_json(item) for item in items]
    return {ITEM_KEY: Item(items).value}


def _from_json(items: Any) -> Any:
    """Recursively convert loaded JSON back into Items.

    Accepts both ``{"__Item__": id}`` objects and bare identifier strings.
    """
    if isinstance(items, list):
        return [_from_json(item) for item in items]
    if isinstance(items, dict):
        return Item(items[ITEM_KEY])
    return Item(items)


def save_items(items: Items, filename: Path | str) -> None:
    """save a Profile, Cuboid or Row to a json file"""

    if isinstance(items, np.ndarray):
        items = items.tolist()  # type: ignore

    if validate(items) == 0:
        raise ValueError("items is not a valid Row, Profile or Cuboid")

    with open(filename, "w", encoding="utf-8") as file:
        json.dump(_to_json(items), file, separators=(",", ":"), indent=4)


def load_items(filename: Path | str, dimensions: int | None = None) -> Items:
    """load a JSON file of Items - returns a Cuboid, Profile or Row"""

    with open(filename, encoding="utf-8") as file:
        result = _from_json(json.load(file))
    valid_dims = validate(result)

    if valid_dims == 0:
        raise ValueError(f"file {filename} contains invalid JSON")

    if dimensions is not None and valid_dims != dimensions:
        raise ValueError(
            f"file {filename} contains {valid_dims} dimension Items "
            f"but {dimensions} dimensions was requested"
        )

    return result


def grab(client: Client, vol: Volume) -> Cuboid:
    """copy blocks from a Volume in the minecraft world into a cuboid of Item"""
    cube: np.ndarray = np.ndarray(vol.size.i_tuple, dtype=Item)

    for idx, _ in np.ndenumerate(cube):
        cube[idx] = get_block(client, vol.start + Vec3(*idx))

    result = cube.tolist()
    return result  # type: ignore
