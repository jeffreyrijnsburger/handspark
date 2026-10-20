"""A small, locally rendered volume of softly lit storm-cloud puffs."""
from functools import lru_cache

import numpy as np
from PIL import Image, ImageFilter


def make_cloud():
    return _cloud().copy()


@lru_cache(maxsize=1)
def _cloud():
    width, height = 700, 240
    yy, xx = np.mgrid[:height, :width].astype(np.float32)
    # Offset front and rear puffs, rather than repeating a row of circles.
    lobes = ((108, 132, 4, 70, 43, 42), (174, 111, 5, 80, 63, 52),
             (248, 99, 9, 91, 72, 58), (340, 84, 12, 82, 65, 52),
             (418, 111, 14, 96, 68, 61), (484, 100, 4, 79, 62, 53),
             (548, 126, 8, 80, 52, 46), (602, 140, 8, 67, 40, 39),
             (195, 144, -30, 66, 39, 36), (287, 139, -31, 75, 43, 40),
             (388, 146, -28, 77, 36, 40), (487, 143, -29, 70, 38, 38),
             (560, 147, -23, 59, 33, 32))
    color = np.zeros((height, width, 3), dtype=np.float32)
    alpha = np.zeros((height, width), dtype=np.float32)
    light = np.array([-0.45, -0.7, -0.6], dtype=np.float32)
    light /= np.linalg.norm(light)
    for z in np.linspace(-91, 78, 32):
        density = np.zeros_like(alpha)
        nx, ny, nz = np.zeros_like(alpha), np.zeros_like(alpha), np.zeros_like(alpha)
        for cx, cy, cz, rx, ry, rz in lobes:
            dx, dy, dz = (xx - cx) / rx, (yy - cy) / ry, (z - cz) / rz
            puff = np.exp(-3 * (dx * dx + dy * dy + dz * dz))
            density += puff
            nx += puff * dx / rx
            ny += puff * dy / ry
            nz += puff * dz / rz
        # Small coherent variations soften the otherwise perfect ellipsoids.
        detail = 0.025 * np.sin(xx * 0.12 + z * 0.08) * np.sin(yy * 0.17 - z * 0.11)
        density = np.clip((density + detail - 0.18) * 3.5, 0, 1)
        norm = np.maximum(1e-6, np.sqrt(nx * nx + ny * ny + nz * nz))
        diffuse = np.maximum(0, (nx * light[0] + ny * light[1] + nz * light[2]) / norm)
        brightness = 0.31 + 0.69 * diffuse
        sample_alpha = 1 - np.exp(-density * 0.42)
        weight = (1 - alpha) * sample_alpha
        for channel, tone in enumerate((211, 222, 238)):
            color[:, :, channel] += weight * (tone * brightness + 9)
        alpha += weight
    rgba = np.zeros((height, width, 4), dtype=np.uint8)
    rgba[:, :, :3] = np.clip(color / np.maximum(alpha[:, :, None], 1e-6), 0, 255)
    rgba[:, :, 3] = np.clip(alpha * 246, 0, 255)
    body = Image.fromarray(rgba).filter(ImageFilter.GaussianBlur(0.8))
    shadow = Image.new('RGBA', body.size, (15, 22, 35, 0))
    shadow.putalpha(body.getchannel('A').filter(ImageFilter.GaussianBlur(7)).point(lambda a: round(a * 0.3)))
    cloud = Image.new('RGBA', body.size)
    cloud.alpha_composite(shadow, (0, 7))
    cloud.alpha_composite(body)
    return cloud
