import math
import random

import numpy as np
from PIL import Image, ImageDraw, ImageFilter


class OrbitalSalute:
    def __init__(self, width=960, height=540, duration=5):
        self.width, self.height, self.duration = width, height, duration
        rng = random.Random(596)
        self.stars = [(rng.random() * math.tau, rng.uniform(25, 520),
                       rng.uniform(0.4, 1.1), rng.choice(((112, 231, 221), (168, 161, 255), (215, 239, 255))))
                      for _ in range(180)]
        self.hand = self.make_hand()

    @staticmethod
    def make_hand():
        mask = Image.new('L', (220, 240))
        draw = ImageDraw.Draw(mask)
        draw.rounded_rectangle((73, 100, 157, 191), radius=30, fill=255)
        draw.rounded_rectangle((94, 167, 140, 222), radius=13, fill=255)
        for a, b, width in (((89, 125), (62, 45), 20), ((107, 113), (86, 29), 20),
                            ((127, 113), (146, 29), 20), ((145, 126), (166, 50), 18),
                            ((86, 148), (40, 114), 22)):
            draw.line((a, b), fill=255, width=width)
            for x, y in (a, b):
                r = width / 2
                draw.ellipse((x - r, y - r, x + r, y + r), fill=255)
        yy, xx = np.mgrid[:240, :220]
        rgba = np.zeros((240, 220, 4), dtype=np.uint8)
        for c, value in enumerate((181, 226, 235)):
            rgba[:, :, c] = np.clip(value + 25 * np.sin(yy / 110) + 17 * np.cos(xx / 90), 0, 255)
        rgba[:, :, 3] = np.asarray(mask.filter(ImageFilter.GaussianBlur(0.6)))
        halo = Image.new('RGBA', mask.size, (59, 221, 211, 0))
        halo.putalpha(mask.filter(ImageFilter.GaussianBlur(8)).point(lambda a: round(a * 0.55)))
        halo.alpha_composite(Image.fromarray(rgba))
        return halo

    def frame(self, t):
        frame = Image.new('RGBA', (self.width, self.height))
        fade = max(0, min(1, t / 0.35, (self.duration - t) / 0.7))
        if not fade:
            return frame
        trails = Image.new('RGBA', frame.size)
        draw = ImageDraw.Draw(trails)
        cx, cy = self.width * 0.53, self.height * 0.46
        for angle, start, speed, color in self.stars:
            r = 35 + (start + t * speed * 95) % 540
            tail = max(25, r - (8 + r * 0.05) * speed)
            x, y = cx + math.cos(angle) * r, cy + math.sin(angle) * r * 0.64
            draw.line((cx + math.cos(angle) * tail, cy + math.sin(angle) * tail * 0.64, x, y),
                      fill=(*color, round(180 * min(1, r / 180))), width=2)
        for i in range(3):
            radius = 125 + i * 23 + 4 * math.sin(t * 1.8 + i)
            box = (cx - radius, cy - radius * 0.61, cx + radius, cy + radius * 0.61)
            start = (t * 25 + i * 115) % 360
            draw.arc(box, start, start + 195, fill=((90, 223, 208, 170) if i % 2 else (157, 135, 248, 155)), width=3)
        frame.alpha_composite(trails.filter(ImageFilter.GaussianBlur(5)))
        frame.alpha_composite(trails)
        side = max(1, round(self.hand.width * min(1, t / 0.5)))
        hand = self.hand.resize((side, round(side * self.hand.height / self.hand.width)), Image.Resampling.LANCZOS)
        frame.alpha_composite(hand, (round(self.width * 0.18 - hand.width / 2),
                                     round(self.height * 0.4 - hand.height / 2 + 3 * math.sin(t * 2))))
        frame.putalpha(frame.getchannel('A').point(lambda a: round(a * fade)))
        return frame
