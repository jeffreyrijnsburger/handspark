"""Render original transparent animations for Apple's documented reactions.

Apple's support images are visual references, not assets shipped by this app.
The animations are procedural; the two hand silhouettes use Apache-2.0 Noto
Emoji artwork already included in emoji/.
"""

import argparse
import math
from pathlib import Path
import random
import subprocess

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

from reactions import ASSET_DIR, REACTIONS

WIDTH, HEIGHT, FPS, DURATION = 960, 540, 24, 5
BASE = Path(__file__).resolve().parent
PALETTE = [(255, 75, 115), (50, 185, 255), (255, 205, 65),
           (135, 100, 255), (70, 235, 160), (255, 135, 55)]


def envelope(t):
    return max(0.0, min(1.0, t / 0.3, (DURATION - t) / 0.65))


def opacity(image, value):
    if value >= 0.999:
        return image
    result = image.copy()
    result.putalpha(image.getchannel('A').point(lambda a: round(a * max(0.0, value))))
    return result


def shaded_shape(kind, color, size=192):
    yy, xx = np.mgrid[0:size, 0:size].astype(np.float32)
    x, y = (xx / size - 0.5) * 2, (yy / size - 0.5) * 2
    mask = Image.new('L', (size * 3, size * 3))
    draw = ImageDraw.Draw(mask)
    if kind == 'heart':
        points = []
        for index in range(360):
            a = index * math.tau / 360
            hx = 16 * math.sin(a) ** 3
            hy = 13 * math.cos(a) - 5 * math.cos(2 * a) - 2 * math.cos(3 * a) - math.cos(4 * a)
            points.append(((hx / 36 + 0.5) * size * 3, (0.46 - hy / 36) * size * 3))
        draw.polygon(points, fill=255)
    else:
        draw.ellipse((size * 0.20, size * 0.10, size * 2.80, size * 2.72), fill=255)
    mask = mask.resize((size, size), Image.Resampling.LANCZOS)
    body = 0.58 + 0.42 * np.sqrt(np.maximum(0, 1 - (x * 0.9) ** 2 - (y * 0.8) ** 2))
    highlight = np.exp(-((x + 0.32) ** 2 / 0.045 + (y + 0.4) ** 2 / 0.09)) * 0.72
    rgba = np.zeros((size, size, 4), dtype=np.uint8)
    for channel in range(3):
        rgba[:, :, channel] = np.clip(color[channel] * body * (1 - highlight) + 255 * highlight, 0, 255)
    rgba[:, :, 3] = np.asarray(mask)
    return Image.fromarray(rgba)


class Renderer:
    def __init__(self, reaction):
        self.reaction = reaction
        self.rng = random.Random(2026)
        self.particles = []
        if reaction == 'heart':
            sprite = shaded_shape('heart', (255, 35, 60))
            for i in range(16):
                size = self.rng.randint(55, 108)
                image = sprite.resize((size, size), Image.Resampling.LANCZOS)
                self.particles.append((image, i * 0.07, self.rng.uniform(-1, 1), self.rng.random() * math.tau))
        elif reaction in ('thumbs_up', 'thumbs_down'):
            self.bubble = self.make_bubble(reaction)
        elif reaction == 'balloons':
            for i in range(12):
                width = self.rng.randint(90, 175)
                color = PALETTE[i % len(PALETTE)]
                sprite = shaded_shape('balloon', color).resize((width, int(width * 1.25)), Image.Resampling.LANCZOS)
                side = self.rng.choice((self.rng.uniform(-0.03, 0.23), self.rng.uniform(0.74, 0.96)))
                self.particles.append((sprite, side * WIDTH, self.rng.uniform(0.0, 1.4), self.rng.uniform(175, 260), color))
        elif reaction == 'confetti':
            for i in range(220):
                side = i % 2
                self.particles.append((side, self.rng.uniform(0, 0.7),
                                       self.rng.uniform(65, 380) * (1 if side == 0 else -1),
                                       self.rng.uniform(-740, -420), self.rng.uniform(6, 13),
                                       self.rng.uniform(0, math.tau), PALETTE[i % len(PALETTE)]))
        elif reaction == 'fireworks':
            self.bursts = []
            for i, (x, y, spawn) in enumerate(((0.19, 0.38, 0.35), (0.80, 0.28, 0.95),
                                              (0.47, 0.16, 1.7), (0.77, 0.53, 2.7), (0.20, 0.22, 3.2))):
                sparks = [(self.rng.uniform(0, math.tau), self.rng.uniform(180, 460),
                           self.rng.uniform(0.75, 1.0)) for _ in range(170)]
                colors = [(255, 195, 70), (255, 215, 145), (135, 195, 255),
                          (255, 120, 185), (135, 255, 200)]
                self.bursts.append((x * WIDTH, y * HEIGHT, spawn, colors[i], sparks))
        elif reaction == 'rain':
            self.cloud = self.make_cloud()
            self.particles = [(self.rng.uniform(0.18, 0.82) * WIDTH,
                               self.rng.uniform(0, HEIGHT), self.rng.uniform(450, 750),
                               self.rng.uniform(8, 22)) for _ in range(180)]

    def make_bubble(self, reaction):
        size = 208
        bubble = Image.new('RGBA', (size, size))
        shaded = shaded_shape('balloon', (175, 182, 196), 182)
        shaded.putalpha(shaded.getchannel('A').point(lambda a: round(a * 0.83)))
        bubble.alpha_composite(shaded, (24, 1))
        draw = ImageDraw.Draw(bubble)
        draw.ellipse((32, 5, 201, 169), outline=(245, 248, 255, 170), width=2)
        draw.ellipse((13, 165, 41, 193), fill=(174, 182, 197, 185), outline=(250, 250, 255, 120), width=2)
        draw.ellipse((2, 192, 15, 205), fill=(174, 182, 197, 155))
        name = 'emoji_u1f44d.png' if reaction == 'thumbs_up' else 'emoji_u1f44e.png'
        hand = Image.open(BASE / 'emoji' / name).convert('RGBA').resize((114, 114), Image.Resampling.LANCZOS)
        white = Image.new('RGBA', hand.size, (255, 255, 255))
        white.putalpha(hand.getchannel('A'))
        bubble.alpha_composite(white, (55, 32))
        return bubble

    def make_cloud(self):
        cloud = Image.new('RGBA', (620, 155))
        draw = ImageDraw.Draw(cloud)
        for i in range(12):
            x = 30 + i * 46
            y = 18 + 13 * math.sin(i * 1.8)
            draw.ellipse((x - 45, y, x + 72, y + 110), fill=(121, 130, 145, 205))
        draw.rounded_rectangle((30, 65, 590, 125), radius=35, fill=(115, 123, 137, 210))
        return cloud.filter(ImageFilter.GaussianBlur(7))

    def frame(self, t):
        method = getattr(self, self.reaction)
        return method(t)

    def heart(self, t):
        frame = Image.new('RGBA', (WIDTH, HEIGHT))
        for image, spawn, drift, phase in self.particles:
            age = t - spawn
            if age <= 0:
                continue
            x = WIDTH * 0.5 + drift * (20 + age * 38) + 12 * math.sin(age * 1.6 + phase)
            y = HEIGHT * 0.75 - age * 90
            scale = min(1, age / 0.3)
            size = max(1, round(image.width * scale))
            sprite = image.resize((size, size), Image.Resampling.LANCZOS)
            sprite = opacity(sprite, min(envelope(t), age / 0.2))
            frame.alpha_composite(sprite, (round(x - size / 2), round(y - size / 2)))
        return frame

    def thumbs_up(self, t):
        return self.thumb_frame(t)

    def thumbs_down(self, t):
        return self.thumb_frame(t)

    def thumb_frame(self, t):
        frame = Image.new('RGBA', (WIDTH, HEIGHT))
        pop = min(1.0, max(0, t / 0.45))
        scale = 1 - (1 - pop) ** 3
        side = max(1, round(self.bubble.width * scale))
        image = opacity(self.bubble.resize((side, side), Image.Resampling.LANCZOS), envelope(t))
        frame.alpha_composite(image, (round(WIDTH / 2 - side / 2), round(HEIGHT / 2 - side / 2)))
        return frame

    def balloons(self, t):
        frame = Image.new('RGBA', (WIDTH, HEIGHT))
        draw = ImageDraw.Draw(frame)
        for sprite, x, spawn, speed, color in self.particles:
            age = t - spawn
            if age < 0:
                continue
            cx = x + 12 * math.sin(age * 1.4 + spawn)
            y = HEIGHT + 15 - age * speed
            bottom = y + sprite.height * 0.95
            string = [(round(cx + sprite.width / 2 + 8 * math.sin(k * 0.45 + age * 2)),
                       round(bottom + k * 5)) for k in range(24)]
            draw.line(string, fill=(210, 218, 229, round(150 * envelope(t))), width=1)
            draw.polygon([(cx + sprite.width * 0.47, bottom - 2),
                          (cx + sprite.width * 0.53, bottom - 2),
                          (cx + sprite.width * 0.5, bottom + 7)], fill=(*color, round(235 * envelope(t))))
            frame.alpha_composite(opacity(sprite, envelope(t) * 0.94), (round(cx), round(y)))
        return frame

    def confetti(self, t):
        frame = Image.new('RGBA', (WIDTH, HEIGHT))
        draw = ImageDraw.Draw(frame)
        for side, spawn, vx, vy, size, phase, color in self.particles:
            age = t - spawn
            if age < 0:
                continue
            x = WIDTH * (0.06 if side == 0 else 0.94) + vx * age + 20 * math.sin(age * 2 + phase)
            y = HEIGHT * 1.03 + vy * age + 0.5 * 325 * age * age
            if not (-20 < x < WIDTH + 20 and -20 < y < HEIGHT + 20):
                continue
            angle = phase + age * 3.5
            dx, dy = size * math.cos(angle), size * math.sin(angle)
            nx, ny = -dy * 0.35, dx * 0.35
            draw.polygon([(x - dx + nx, y - dy + ny), (x + dx + nx, y + dy + ny),
                          (x + dx - nx, y + dy - ny), (x - dx - nx, y - dy - ny)],
                         fill=(*color, round(245 * envelope(t))))
        return frame

    def fireworks(self, t):
        fade = envelope(t)
        frame = Image.new('RGBA', (WIDTH, HEIGHT), (5, 7, 20, round(68 * fade)))
        trails = Image.new('RGBA', frame.size)
        draw = ImageDraw.Draw(trails)
        for x, y, spawn, color, sparks in self.bursts:
            age = t - spawn
            if -0.35 < age < 0:
                progress = (age + 0.35) / 0.35
                ry = HEIGHT + (y - HEIGHT) * progress
                draw.line((x, ry, x, ry + 35), fill=(*color, round(180 * fade)), width=2)
            if age < 0 or age > 2.4:
                continue
            alpha = fade * max(0, 1 - age / 2.4) ** 0.65
            distance = (1 - math.exp(-age * 1.4)) / 1.4
            for angle, speed, brightness in sparks:
                vx, vy = math.cos(angle) * speed, math.sin(angle) * speed
                sx, sy = x + vx * distance, y + vy * distance + 27 * age * age
                before = max(0, age - 0.20)
                d0 = (1 - math.exp(-before * 1.4)) / 1.4
                ex, ey = x + vx * d0, y + vy * d0 + 27 * before * before
                c = tuple(round(v * 0.55 + 255 * 0.45) for v in color)
                draw.line((ex, ey, sx, sy), fill=(*color, round(255 * alpha * brightness)), width=4)
                draw.line((ex, ey, sx, sy), fill=(*c, round(255 * alpha)), width=1)
                draw.ellipse((sx - 2, sy - 2, sx + 2, sy + 2), fill=(255, 250, 225, round(255 * alpha)))
        glow = trails.filter(ImageFilter.GaussianBlur(5))
        glow.putalpha(glow.getchannel('A').point(lambda a: min(255, round(a * 2.5))))
        frame = Image.alpha_composite(frame, glow)
        return Image.alpha_composite(frame, trails)

    def rain(self, t):
        fade = envelope(t)
        frame = Image.new('RGBA', (WIDTH, HEIGHT), (15, 23, 38, round(28 * fade)))
        frame.alpha_composite(opacity(self.cloud, fade), (round((WIDTH - self.cloud.width) / 2), 0))
        draw = ImageDraw.Draw(frame)
        for x, offset, speed, length in self.particles:
            y = 90 + (offset + t * speed) % (HEIGHT - 70)
            dx = -length * 0.16
            draw.line((x, y, x + dx, y + length), fill=(195, 215, 239, round(115 * fade)), width=1)
        return frame

    def lasers(self, t):
        fade = envelope(t)
        frame = Image.new('RGBA', (WIDTH, HEIGHT), (4, 3, 18, round(62 * fade)))
        beams, glow = Image.new('RGBA', frame.size), Image.new('RGBA', frame.size)
        draw, light = ImageDraw.Draw(beams), ImageDraw.Draw(glow)
        colors = [(20, 255, 110), (40, 175, 255), (215, 50, 255), (255, 60, 145)]
        for side in (0, 1):
            origin = (WIDTH * (0.04 if side == 0 else 0.96), HEIGHT * 1.04)
            for beam in range(4):
                phase = t * (0.62 + beam * 0.12) + beam * 0.77 + side * 1.9
                end = (WIDTH * (0.5 + 1.05 * math.sin(phase)), -HEIGHT * 0.35)
                color = colors[(beam + side) % len(colors)]
                light.line([origin, end], fill=(*color, round(105 * fade)), width=18)
                draw.line([origin, end], fill=(*color, round(130 * fade)), width=5)
                draw.line([origin, end], fill=(*color, round(240 * fade)), width=2)
        frame = Image.alpha_composite(frame, glow.filter(ImageFilter.GaussianBlur(9)))
        return Image.alpha_composite(frame, beams)


def render(reaction):
    ASSET_DIR.mkdir(exist_ok=True)
    output = ASSET_DIR / (reaction + '.mov')
    temporary = ASSET_DIR / (reaction + '.tmp.mov')
    renderer = Renderer(reaction)
    encoder = subprocess.Popen([
        'ffmpeg', '-hide_banner', '-loglevel', 'error', '-y',
        '-f', 'rawvideo', '-pixel_format', 'rgba', '-video_size', f'{WIDTH}x{HEIGHT}',
        '-framerate', str(FPS), '-i', '-', '-an', '-c:v', 'qtrle', '-pix_fmt', 'argb',
        '-threads', '1', '-movflags', '+faststart', str(temporary),
    ], stdin=subprocess.PIPE)
    try:
        for index in range(FPS * DURATION):
            encoder.stdin.write(renderer.frame(index / FPS).tobytes())
        encoder.stdin.close()
        if encoder.wait() != 0:
            raise RuntimeError(f'{reaction}: video encoding failed')
        temporary.replace(output)
    except BaseException:
        encoder.kill()
        encoder.wait()
        temporary.unlink(missing_ok=True)
        raise
    print(f'{reaction}: {output.stat().st_size:,} bytes', flush=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('reaction', choices=(*REACTIONS, 'all'))
    args = parser.parse_args()
    for reaction in (REACTIONS if args.reaction == 'all' else [args.reaction]):
        render(reaction)


if __name__ == '__main__':
    main()
