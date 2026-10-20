"""A golden thumbs-up with a spring entrance and a small celebratory burst."""
import math
from pathlib import Path
import random

import numpy as np
from PIL import Image, ImageDraw, ImageFilter


class ThumbsUp:
    def __init__(self, width=960, height=540, duration=5):
        self.width, self.height, self.duration = width, height, duration
        self.badge = self.make_badge()
        source = Path(__file__).resolve().parent / 'emoji/emoji_u1f44d.png'
        self.hand = Image.open(source).convert('RGBA').resize((160, 160), Image.Resampling.LANCZOS)
        rng = random.Random(44)
        palette = ((255, 204, 86), (84, 230, 183), (105, 190, 255), (255, 132, 143))
        self.bits = [(i * math.tau / 22 + rng.uniform(-0.1, 0.1), rng.uniform(90, 155),
                      rng.uniform(4, 7), palette[i % len(palette)]) for i in range(22)]
        self.bubble = self.pose(1.5)

    @staticmethod
    def make_badge():
        size = 272
        yy, xx = np.mgrid[:size, :size].astype(np.float32)
        x, y = (xx - 136) / 108, (yy - 132) / 108
        mask = Image.new('L', (size * 2, size * 2))
        ImageDraw.Draw(mask).ellipse((56, 48, 488, 480), fill=255)
        mask = mask.resize((size, size), Image.Resampling.LANCZOS)
        dome = np.sqrt(np.maximum(0, 1 - x * x - y * y))
        sheen = np.exp(-((x + 0.45) / 0.7) ** 2 - ((y + 0.55) / 0.5) ** 2)
        rgba = np.zeros((size, size, 4), dtype=np.uint8)
        for c, base in enumerate((24, 119, 130)):
            rgba[:, :, c] = np.clip(base + 50 * dome + 95 * sheen, 0, 255)
        rgba[:, :, 3] = np.asarray(mask) * 0.9
        badge = Image.new('RGBA', (size, size))
        glow = Image.new('RGBA', (size, size), (43, 212, 189, 0))
        glow.putalpha(mask.filter(ImageFilter.GaussianBlur(7)).point(lambda a: round(a * 0.18)))
        badge.alpha_composite(glow)
        badge.alpha_composite(Image.fromarray(rgba))
        rim = Image.new('RGBA', (size * 2, size * 2))
        draw = ImageDraw.Draw(rim)
        draw.ellipse((56, 48, 488, 480), outline=(116, 244, 208, 205), width=5)
        draw.arc((65, 57, 479, 471), 192, 285, fill=(235, 255, 242, 225), width=6)
        draw.arc((69, 61, 475, 467), 24, 90, fill=(255, 213, 113, 180), width=4)
        badge.alpha_composite(rim.resize(badge.size, Image.Resampling.LANCZOS))
        return badge

    def pose(self, t):
        badge = self.badge.copy()
        nod = max(0, t - 1.5)
        angle = -8 * math.exp(-t * 2) * math.sin(t * 12)
        angle += 8 * math.sin(nod * 9) * math.exp(-nod * 3) if nod else 0
        hand = self.hand.rotate(angle, Image.Resampling.BICUBIC, expand=True)
        x = round(136 - hand.width / 2)
        y = round(127 - hand.height / 2 - 3 * math.sin(t * 2.4))
        depth = Image.new('RGBA', hand.size, (153, 83, 13, 0))
        depth.putalpha(hand.getchannel('A').point(lambda a: round(a * 0.85)))
        shadow = Image.new('RGBA', hand.size, (3, 31, 48, 0))
        shadow.putalpha(hand.getchannel('A').filter(ImageFilter.GaussianBlur(4)).point(lambda a: round(a * 0.6)))
        badge.alpha_composite(shadow, (x + 2, y + 9))
        badge.alpha_composite(depth, (x + 1, y + 4))
        badge.alpha_composite(hand, (x, y))
        return badge

    def frame(self, t):
        frame = Image.new('RGBA', (self.width, self.height))
        fade = max(0, min(1, t / 0.18, (self.duration - t) / 0.65))
        if not fade:
            return frame
        cx, cy = self.width / 2, self.height / 2
        marks = Image.new('RGBA', frame.size)
        draw = ImageDraw.Draw(marks)
        age = t - 0.12
        if 0 < age < 1.2:
            a = fade * (1 - age / 1.2) ** 1.3
            for angle, speed, size, color in self.bits:
                radius = 115 + speed * (1 - math.exp(-age * 3)) / 3
                x = cx + math.cos(angle) * radius
                y = cy + math.sin(angle) * radius * 0.75 + 14 * age * age
                draw.ellipse((x - size / 2, y - size / 2, x + size / 2, y + size / 2),
                             fill=(*color, round(255 * a)))
        for i in range(7):
            phase = t - 0.18 - i * 0.035
            if not 0 < phase < 0.7:
                continue
            angle = -math.pi + i * math.pi / 6
            radius = 120 + 38 * phase
            a = fade * (1 - phase / 0.7)
            draw.line((cx + math.cos(angle) * radius, cy + math.sin(angle) * radius * 0.8,
                       cx + math.cos(angle) * (radius + 14), cy + math.sin(angle) * (radius + 14) * 0.8),
                      fill=(255, 217, 120, round(240 * a)), width=4)
        frame.alpha_composite(marks)
        spring = max(0.01, min(1.12, 1 - math.exp(-t * 7) * math.cos(t * 14)))
        image = self.pose(t)
        side = max(1, round(image.width * spring))
        image = image.resize((side, side), Image.Resampling.LANCZOS)
        image.putalpha(image.getchannel('A').point(lambda a: round(a * fade)))
        bounce = -9 * math.exp(-t * 3) * math.sin(t * 13) + 2 * math.sin(t * 2)
        frame.alpha_composite(image, (round(cx - side / 2), round(cy - side / 2 + bounce)))
        return frame
