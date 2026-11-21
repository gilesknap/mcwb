from pathlib import Path
from unittest import TestCase

from mcwb.api import polygon
from mcwb.item import Item
from mcwb.itemlists import grab, load_items
from mcwb.polygon import poly_profile
from mcwb.types import Anchor3, Direction, Vec3
from mcwb.volume import Volume
from tests.mockclient import MockClient


class TestPoly(TestCase):
    def test_poly(self):
        client = MockClient(size=20)

        center = Vec3(x=0, y=0, z=0)
        corner = Vec3(x=-2, y=0, z=-2)

        polygon(
            client,  # type: ignore
            center=center,
            sides=4,
            height=2,
            diameter=5,
            item=Item.BLUE_CONCRETE,
            offset=None,
            direction=Direction.UP,
        )

        # test against a saved cube
        cube_path = Path("tests/cubes/poly.cube")
        expected = load_items(cube_path)

        # also test using the grab function
        vol = Volume.from_anchor(center, Vec3(5, 5, 5), Anchor3.BOTTOM_CENTER)
        cuboid = grab(
            client,  # type: ignore
            vol,
        )

        assert client.compare(corner, expected)

        assert cuboid == expected

    def test_filled_poly(self):
        client = MockClient(size=20)

        center = Vec3(x=0, y=0, z=0)
        corner = Vec3(x=-2, y=0, z=-2)

        polygon(
            client,  # type: ignore
            center=center,
            sides=4,
            height=2,
            diameter=5,
            item=Item.BLUE_CONCRETE,
            offset=None,
            direction=Direction.UP,
            fill_item=Item.RED_CONCRETE,
        )

        # test against a saved cube
        cube_path = Path("tests/cubes/polyfill.cube")
        expected = load_items(cube_path)

        assert client.compare(corner, expected)

    def test_odd_sided_profile_does_not_wrap(self):
        # a triangle with its apex up: the apex is alone in the first row and
        # the base fills the last row, rather than wrapping round the profile
        profile = poly_profile(sides=3, diameter=15, item=Item.STONE)

        apex = [z for z, block in enumerate(profile[0]) if block != Item.AIR]
        assert apex == [profile.shape[1] // 2]
        assert all(block == Item.STONE for block in profile[-1])
