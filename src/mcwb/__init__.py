"""Top level API.

.. data:: __version__
    :type: str

    Version number as calculated by https://github.com/pypa/setuptools_scm
"""

from mcwb.api import get_block, make_tunnel, polygon
from mcwb.blocks import Blocks
from mcwb.types import (
    Anchor,
    Anchor3,
    Anchor3Face,
    Cuboid,
    Direction,
    Items,
    Planes3d,
    Profile,
    Row,
    Vec3,
)
from mcwb.volume import Volume

from ._version import __version__

__all__ = [
    "__version__",
    "Anchor",
    "Anchor3",
    "Anchor3Face",
    "Blocks",
    "Cuboid",
    "Direction",
    "Items",
    "Planes3d",
    "Profile",
    "Row",
    "Vec3",
    "Volume",
    "make_tunnel",
    "polygon",
    "get_block",
]
