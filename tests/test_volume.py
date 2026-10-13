from itertools import product
from unittest import TestCase

from mcipc.rcon.enumerations import FillMode

from mcwb import Anchor3, Vec3, Volume
from mcwb.item import Item
from mcwb.volume import MAX_MINECRAFT_FILL_COMMAND
from tests.mockclient import MockClient


class TestVolume(TestCase):
    """Tests the Volume constructor."""

    def test_anchors_odd_size(self):
        size = Vec3(3, 3, 3)
        position = Vec3(0, 0, 0)

        v = Volume.from_anchor(position, size, anchor=Anchor3.MIDDLE)
        self.assertTrue(v.position == position)
        self.assertTrue(v.start == Vec3(-1, -1, -1))
        self.assertTrue(v.end == Vec3(1, 1, 1))
        self.assertTrue(v.size == size)

        v = Volume.from_anchor(position, size, anchor=Anchor3.BOTTOM_NW)
        self.assertTrue(v.position == position)
        self.assertTrue(v.start == Vec3(0, 0, 0))
        self.assertTrue(v.end == Vec3(2, 2, 2))
        self.assertTrue(v.size == size)

        v = Volume.from_anchor(position, size, anchor=Anchor3.BOTTOM_NE)
        self.assertTrue(v.position == position)
        self.assertTrue(v.start == Vec3(-2, 0, 0))
        self.assertTrue(v.end == Vec3(0, 2, 2))
        self.assertTrue(v.size == size)

        v = Volume.from_anchor(position, size, anchor=Anchor3.BOTTOM_SE)
        self.assertTrue(v.position == position)
        self.assertTrue(v.start == Vec3(-2, 0, -2))
        self.assertTrue(v.end == Vec3(0, 2, 0))
        self.assertTrue(v.size == size)

        v = Volume.from_anchor(position, size, anchor=Anchor3.BOTTOM_SW)
        self.assertTrue(v.position == position)
        self.assertTrue(v.start == Vec3(0, 0, -2))
        self.assertTrue(v.end == Vec3(2, 2, 0))
        self.assertTrue(v.size == size)

        v = Volume.from_anchor(position, size, anchor=Anchor3.BOTTOM_MIDDLE)
        self.assertTrue(v.position == position)
        self.assertTrue(v.start == Vec3(-1, 0, -1))
        self.assertTrue(v.end == Vec3(1, 2, 1))
        self.assertTrue(v.size == size)

        v = Volume.from_anchor(position, size, anchor=Anchor3.TOP_NW)
        self.assertTrue(v.position == position)
        self.assertTrue(v.start == Vec3(0, -2, 0))
        self.assertTrue(v.end == Vec3(2, 0, 2))
        self.assertTrue(v.size == size)

        v = Volume.from_anchor(position, size, anchor=Anchor3.TOP_NE)
        self.assertTrue(v.position == position)
        self.assertTrue(v.start == Vec3(-2, -2, 0))
        self.assertTrue(v.end == Vec3(0, 0, 2))
        self.assertTrue(v.size == size)

        v = Volume.from_anchor(position, size, anchor=Anchor3.TOP_SE)
        self.assertTrue(v.position == position)
        self.assertTrue(v.start == Vec3(-2, -2, -2))
        self.assertTrue(v.end == Vec3(0, 0, 0))
        self.assertTrue(v.size == size)

        v = Volume.from_anchor(position, size, anchor=Anchor3.TOP_SW)
        self.assertTrue(v.position == position)
        self.assertTrue(v.start == Vec3(0, -2, -2))
        self.assertTrue(v.end == Vec3(2, 0, 0))
        self.assertTrue(v.size == size)

        v = Volume.from_anchor(position, size, anchor=Anchor3.TOP_MIDDLE)
        self.assertTrue(v.position == position)
        self.assertTrue(v.start == Vec3(-1, -2, -1))
        self.assertTrue(v.end == Vec3(1, 0, 1))
        self.assertTrue(v.size == size)

    def test_anchors_even_size(self):
        size = Vec3(4, 4, 4)
        position = Vec3(0, 0, 0)

        v = Volume.from_anchor(position, size, anchor=Anchor3.MIDDLE)
        self.assertTrue(v.position == position)
        self.assertTrue(v.start == Vec3(-2, -2, -2))
        self.assertTrue(v.end == Vec3(1, 1, 1))
        self.assertTrue(v.size == size)

        v = Volume.from_anchor(position, size, anchor=Anchor3.BOTTOM_NW)
        self.assertTrue(v.position == position)
        self.assertTrue(v.start == Vec3(0, 0, 0))
        self.assertTrue(v.end == Vec3(3, 3, 3))
        self.assertTrue(v.size == size)

        v = Volume.from_anchor(position, size, anchor=Anchor3.BOTTOM_NE)
        self.assertTrue(v.position == position)
        self.assertTrue(v.start == Vec3(-3, 0, 0))
        self.assertTrue(v.end == Vec3(0, 3, 3))
        self.assertTrue(v.size == size)

    def test_bounds_odd_size(self):
        size = Vec3(3, 3, 3)
        position = Vec3(-1, -1, -1)

        for x, y, z in product([1, -1], [1, -1], [1, -1]):
            start = Vec3(x, y, z)
            opposite = Vec3(-x, -y, -z)
            print(start, opposite)
            v = Volume.from_corners(start, end=opposite)
            print(v.start, v.end, v.position, v.size)
            self.assertTrue(v.position == position)
            self.assertTrue(v.size == size)


class TestVolumeFill(TestCase):
    """Volume.fill replaces every block, whatever the volume's size."""

    def check_fill(self, size: Vec3):
        client = MockClient()
        start = Vec3(-20, -20, -20)
        vol = Volume.from_anchor(start, size, anchor=Anchor3.BOTTOM_NW)
        # existing terrain, with an air pocket, overlapping the volume
        client.fill(start, start + Vec3(size.x, 5, size.z), Item.STONE)
        client.setblock(start + Vec3(1, 1, 1), Item.AIR)

        vol.fill(client, Item.GOLD_BLOCK)  # type: ignore
        x, y, z = int(size.x), int(size.y), int(size.z)
        self.assertTrue(client.compare(start, [[[Item.GOLD_BLOCK] * z] * y] * x))
        # nothing outside the volume changed
        self.assertEqual(client.getblock(start + Vec3(x, 0, 0)), Item.STONE)
        self.assertEqual(client.getblock(start + Vec3(0, y, 0)), Item.AIR)

        vol.fill(client, Item.AIR)  # type: ignore
        self.assertTrue(client.compare(start, [[[Item.AIR] * z] * y] * x))
        self.assertEqual(client.getblock(start + Vec3(x, 0, 0)), Item.STONE)

    def test_small_fill_replaces(self):
        self.check_fill(Vec3(5, 6, 7))

    def test_large_fill_replaces(self):
        size = Vec3(40, 25, 35)
        self.assertGreaterEqual(size.x * size.y * size.z, MAX_MINECRAFT_FILL_COMMAND)
        self.check_fill(size)

    def test_huge_fill_splits_into_legal_commands(self):
        """every /fill is under the server's limit and the boxes tile the volume"""

        class Recorder:
            def __init__(self):
                self.boxes = []

            def fill(self, start, end, block, mode=None, filter=None):
                self.boxes.append((start, end, mode))

        for size in (Vec3(300, 5, 300), Vec3(40000, 1, 1), Vec3(181, 181, 3)):
            client = Recorder()
            start = Vec3(-7, 3, 11)
            Volume.from_anchor(start, size, anchor=Anchor3.BOTTOM_NW).fill(
                client,  # type: ignore
                Item.STONE,
            )
            covered = set()
            for a, b, mode in client.boxes:
                self.assertEqual(mode, FillMode.REPLACE)
                box = Volume.from_corners(a, b)
                self.assertLess(box.size.volume, MAX_MINECRAFT_FILL_COMMAND)
                for c in product(
                    *(range(lo, hi + 1) for lo, hi in zip(a, b, strict=True))
                ):
                    self.assertNotIn(c, covered)
                    covered.add(c)
            self.assertEqual(len(covered), size.volume)
            self.assertEqual(min(covered), tuple(start))
            self.assertEqual(max(covered), tuple(start + size - 1))
