"""Regenerate src/mcwb/item.py from an official Minecraft Java Edition release.

The block and item identifiers are read from the file names of the
``assets/minecraft/items/*.json`` and ``assets/minecraft/blockstates/*.json``
entries in Mojang's client jar, so no Java runtime is required.

Usage::

    uv run python scripts/generate_items.py            # latest release
    uv run python scripts/generate_items.py 26.3       # a specific version
"""

import argparse
import hashlib
import io
import json
import re
import subprocess
import sys
import urllib.request
import zipfile
from pathlib import Path

MANIFEST = "https://piston-meta.mojang.com/mc/game/version_manifest_v2.json"
OUTPUT = Path(__file__).parent.parent / "src" / "mcwb" / "item.py"
ID_PATTERN = re.compile(
    r"assets/minecraft/(?:items|blockstates)/([a-z0-9_]+)\.json", re.ASCII
)

HEADER = '''# ruff: noqa: E501
"""Minecraft Java Edition block and item identifiers.

GENERATED FILE - do not edit by hand. Regenerate with
``uv run python scripts/generate_items.py``.

The identifiers come from Minecraft {version}. They replace
``mcipc.rcon.enumerations.Item``, which has not been updated since
Minecraft 1.16 and lacks blocks such as deepslate or cherry planks.
This enum is a ``str`` subclass with the same member names, so its members
compare equal to the matching mcipc members and to plain strings such as
``"minecraft:stone"``, and can be passed to any mcipc command.
"""

from enum import Enum

__all__ = ["MINECRAFT_VERSION", "Item"]

MINECRAFT_VERSION = "{version}"
"""The Minecraft Java Edition release these identifiers were generated from."""

PREFIX = "minecraft:"


class Item(str, Enum):  # noqa: UP042 - mirrors mcipc's Item
    """Minecraft Java Edition blocks and items.

    Lookup by value accepts the identifier with or without the
    ``minecraft:`` prefix, e.g. ``Item("stone") is Item.STONE``.
    """

'''

FOOTER = '''
    @classmethod
    def _missing_(cls, value: object) -> "Item | None":
        """Allow lookup of identifiers without the ``minecraft:`` prefix."""
        if isinstance(value, str) and not value.startswith(PREFIX):
            return cls(f"{PREFIX}{value}")
        return None

    def __str__(self) -> str:
        """Return the namespaced identifier, e.g. ``minecraft:stone``."""
        return self.value
'''


def fetch_json(url: str) -> dict:
    with urllib.request.urlopen(url) as response:
        return json.load(response)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("version", nargs="?", help="defaults to the latest release")
    args = parser.parse_args()

    manifest = fetch_json(MANIFEST)
    version = args.version or manifest["latest"]["release"]
    (entry,) = [v for v in manifest["versions"] if v["id"] == version]
    client = fetch_json(entry["url"])["downloads"]["client"]

    print(f"Downloading Minecraft {version} client jar ...")
    with urllib.request.urlopen(client["url"]) as response:
        jar = response.read()
    if hashlib.sha1(jar).hexdigest() != client["sha1"]:
        raise SystemExit("client jar checksum mismatch")

    names = zipfile.ZipFile(io.BytesIO(jar)).namelist()
    ids = sorted({m[1] for m in map(ID_PATTERN.fullmatch, names) if m})

    members = "".join(f'    {i.upper()} = f"{{PREFIX}}{i}"\n' for i in ids)
    OUTPUT.write_text(HEADER.format(version=version) + members + FOOTER)
    subprocess.run([sys.executable, "-m", "ruff", "format", str(OUTPUT)], check=True)
    print(f"Wrote {len(ids)} identifiers to {OUTPUT}")


if __name__ == "__main__":
    main()
