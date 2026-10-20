"""A procedural concert laser stage with volumetric fans and a perspective floor."""
import math
import random

import numpy as np
from PIL import Image, ImageDraw, ImageFilter


def bloom(image, radius, gain):
    """Keep saturated light at soft edges when exporting straight-alpha video."""
    data = np.asarray(image.filter(ImageFilter.GaussianBlur(radius)), dtype=np.float32).copy()
    alpha = data[:, :, 3:4]
    data[:, :, :3] *= 255 / np.maximum(alpha, 1)
    data[:, :, 3:4] *= gain
    return Image.fromarray(np.clip(data, 0, 255).astype(np.uint8))


def smooth(value):
    value = max(0.0, min(1.0, value))
    return value * value * (3 - 2 * value)


class LaserShow:
    def __init__(self, width=960, height=540, duration=5):
        self.width, self.height, self.duration = width, height, duration
        self.size = width, height
        rng = random.Random(20261020)
        self.dust = [(rng.random(), rng.random(), rng.uniform(0.4, 1), rng.random() * math.tau)
                     for _ in range(48)]
        self.colors = [(30, 255, 180), (38, 200, 255), (130, 95, 255), (255, 50, 190)]

    def frame(self, t):
        fade = smooth(t / 0.35) * smooth((self.duration - t) / 0.7)
        if fade <= 0:
            return Image.new('RGBA', self.size)
        width, height = self.size
        frame = Image.new('RGBA', self.size, (5, 7, 26, round(108 * fade)))
        haze = Image.new('RGBA', self.size)
        rays = Image.new('RGBA', self.size)
        light = Image.new('RGBA', self.size)
        cones = ImageDraw.Draw(haze)
        sharp = ImageDraw.Draw(rays)
        glow = ImageDraw.Draw(light)
        pulse = 0.86 + 0.14 * math.sin(t * math.tau * 1.15) ** 2
        opening = smooth(t / 0.85)
        finale = smooth((t - 2.9) / 0.9)
        # A floor moving towards the viewer gives the fans a shared 3D stage.
        vanishing = (width * 0.5, height * 0.64)
        for lane in range(-7, 8):
            x = width * (0.5 + lane * 0.15)
            sharp.line((vanishing, (x, height * 1.1)), fill=(60, 155, 255, round(42 * fade)), width=1)
        for row in range(10):
            depth = (row / 10 + t * 0.13) % 1
            y = height * (0.64 + depth * depth * 0.48)
            sharp.line((0, y, width, y), fill=(90, 110, 255, round(75 * depth * fade)), width=1)
        for side in (0, 1):
            origin = (width * (0.075 if side == 0 else 0.925), height * 0.935)
            mirror = 1 if side == 0 else -1
            sweep = 0.36 * math.sin(t * 1.65 + side * 1.15)
            fan = (0.05 + 0.075 * opening + 0.018 * finale)
            for index in range(8):
                angle = -math.pi / 2 + 0.45 + sweep + (index - 3.5) * fan
                # Different scan speeds make two fans weave through one another.
                angle += 0.035 * math.sin(t * 3.2 + index * 0.65)
                vx, vy = mirror * math.cos(angle), math.sin(angle)
                end = (origin[0] + vx * height * 2.25, origin[1] + vy * height * 2.25)
                color = self.colors[(index // 2 + side * 2) % len(self.colors)]
                energy = pulse * (0.8 + 0.2 * math.sin(t * 2.1 + index * 0.7) ** 2)
                spread = 13 + 9 * finale
                normal = (-vy * spread, vx * spread)
                cones.polygon((origin, (end[0] + normal[0], end[1] + normal[1]),
                               (end[0] - normal[0], end[1] - normal[1])),
                              fill=(*color, round(19 * energy * fade)))
                glow.line((origin, end), fill=(*color, 255), width=11)
                sharp.line((origin, end), fill=(*color, round(180 * energy * fade)), width=5)
                white = tuple(round(channel * 0.35 + 255 * 0.65) for channel in color)
                sharp.line((origin, end), fill=(*white, round(250 * energy * fade)), width=1)
                # Short afterimages follow each moving beam, rather than flashing.
                trail_angle = angle - 0.035 * math.cos(t * 1.65 + side * 1.15)
                trail = (origin[0] + mirror * math.cos(trail_angle) * height * 2.25,
                         origin[1] + math.sin(trail_angle) * height * 2.25)
                sharp.line((origin, trail), fill=(*color, round(45 * energy * fade)), width=1)
            # Projector rings and anamorphic flare stay anchored to the stage.
            color = self.colors[side * 2 + 1]
            for ring in range(3):
                phase = (t * 0.65 + ring / 3) % 1
                rx, ry = 8 + phase * 82, 3 + phase * 18
                sharp.ellipse((origin[0] - rx, origin[1] - ry, origin[0] + rx, origin[1] + ry),
                              outline=(*color, round((1 - phase) * 145 * fade)), width=2)
            for radius in (32, 15, 6):
                glow.ellipse((origin[0] - radius, origin[1] - radius,
                              origin[0] + radius, origin[1] + radius), fill=(*color, 255))
            sharp.line((origin[0] - 60, origin[1], origin[0] + 60, origin[1]),
                       fill=(*color, round(150 * fade)), width=2)
            sharp.ellipse((origin[0] - 4, origin[1] - 4, origin[0] + 4, origin[1] + 4),
                          fill=(245, 255, 255, round(255 * fade)))
        # Sparse lit haze drifts slowly; the subject remains on the layer above.
        for index, (x, y, speed, phase) in enumerate(self.dust):
            px = (x * width + 18 * math.sin(t * 0.65 + phase)) % width
            py = ((y - t * speed * 0.055) % 1) * height
            alpha = round((0.5 + 0.5 * math.sin(t * 1.4 + phase)) ** 2 * 125 * fade)
            color = self.colors[index % len(self.colors)]
            sharp.ellipse((px - 1, py - 1, px + 1, py + 1), fill=(*color, alpha))
        frame = Image.alpha_composite(frame, haze.filter(ImageFilter.GaussianBlur(5)))
        luminous = bloom(light, 12, 1.35 * fade * pulse)
        frame = Image.alpha_composite(frame, luminous)
        return Image.alpha_composite(frame, rays)
