"""
functions for creating polygons in profiles (2d lists of Items)
"""

import math

import numpy as np

from mcwb.item import Item


def poly_points(diameter: int, sides: int, offset: float | None = None):
    """
    Returns a set of 2d points tp make a polygon with the given diameter and
    number of sides.
    """

    x_points: list[int] = []
    z_points: list[int] = []

    if sides < 3:
        raise ValueError("Number of sides must be at least 3.")

    # calc the radius to the corners
    radius = diameter // 2 / math.sin(math.pi / sides)

    angle = 2 * math.pi / sides
    offset = angle / 2 if offset is None else offset

    for i in range(sides):
        x_points.append(round(radius * math.cos(i * angle + offset)))
        z_points.append(round(radius * math.sin(i * angle + offset)))

    return x_points, z_points


def poly_profile(
    sides=4,
    diameter=15,
    item: Item = Item.STONE,
    offset=None,
    fill_item: Item = Item.AIR,
) -> np.ndarray:
    """
    Create a profile containing a polygon. The dimensions of the profile
    will be just large enough to contain the specified polygon.
    """

    x_points, z_points = poly_points(diameter=diameter, sides=sides, offset=offset)
    x_size = max(x_points) - min(x_points) + 1
    z_size = max(z_points) - min(z_points) + 1
    vertices = list(zip(x_points, z_points, strict=True))

    profile = np.full(shape=(x_size, z_size), fill_value=Item.AIR, dtype=Item)
    center = math.floor(x_size / 2), math.floor(z_size / 2)

    return poly_draw(profile, vertices, center, item, fill_item=fill_item)


def poly_draw(
    profile: np.ndarray,
    vertices: list[tuple[int, int]],
    center: tuple[int, int],
    item: Item,
    fill_item: Item = Item.AIR,
) -> np.ndarray:
    """
    Take a list of 2d points and draw lines between them to make a polygon
    inside of a profile (2d array of Item).
    """

    def add_2d(x: tuple[int, int], z: tuple[int, int]) -> tuple[int, int]:
        return (x[0] + z[0], x[1] + z[1])

    sides = len(vertices)

    for i in range(sides):
        draw_line_xz(
            profile,
            add_2d(center, vertices[i]),
            add_2d(center, vertices[(i + 1) % sides]),
            item,
        )

    if fill_item != Item.AIR:
        for r in range(profile.shape[0]):
            row = profile[r]
            result = np.where(row != Item.AIR)
            positions = result[0]
            if len(positions) == 2:
                row[positions[0] + 1 : positions[1]] = fill_item

    return profile


def draw_line_xz(
    profile: np.ndarray,
    start: tuple[int, int],  # x, z
    end: tuple[int, int],  # x, z
    item: Item = Item.AIR,
    overlap: int = 0,
):
    """
    Creates a line of blocks from start to end inside a 2d profile.
    """

    def delta(n1, n2):
        return (-1, n1 - n2) if n1 > n2 else (1, n2 - n1)

    dir_x, delta_x = delta(start[0], end[0])
    dir_z, delta_z = delta(start[1], end[1])

    steps = max(delta_x, delta_z) or 1

    x_step = delta_x / steps * dir_x
    z_step = delta_z / steps * dir_z

    x, z = start[0], start[1]
    next_x, next_z = x, z

    profile[x][z] = item

    for _i in range(steps + 1):
        if (x, z) != (round(next_x), round(next_z)):
            x, z = round(next_x), round(next_z)
            profile[x][z] = item
        next_z += z_step
        next_x += x_step
