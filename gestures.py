"""Local hand geometry for Apple's eight documented reaction gestures.

https://support.apple.com/nl-nl/105117
Coordinates use the same units on both image axes; thumb direction is relative
to the camera image, while finger extension is invariant to hand rotation.
"""

from dataclasses import dataclass
from itertools import combinations
import math


def _distance(a, b):
    return math.hypot(a[0] - b[0], a[1] - b[1])


def _valid(points):
    return (len(points) == 21
            and all(len(p) >= 2 for p in points)
            and all(math.isfinite(v) for p in points for v in p[:2])
            and _distance(points[5], points[17]) >= 0.005)


def _curled(points, pip, tip):
    return _distance(points[tip], points[0]) < _distance(points[pip], points[0])


def _thumb_direction(points):
    if not _valid(points):
        return None
    # An oblique or loosely closed fist can put a folded fingertip slightly
    # farther from the wrist than its middle joint. Keep the joint-angle
    # check, but do not require every fingertip to fold toward the wrist.
    if not _finger_pattern(points, (False, False, False, False), folded_ratio=1.15):
        return None
    # Palm length keeps the thresholds meaningful when the fist is side-on
    # and its knuckle span is shortened by perspective.
    scale = max(_distance(points[5], points[17]), _distance(points[0], points[9]) * 0.65)
    if (_distance(points[4], points[0]) <= _distance(points[3], points[0]) * 1.05
            or _distance(points[4], points[5]) < scale * 0.5):
        return None
    dx = points[4][0] - points[2][0]
    dy = points[4][1] - points[2][1]
    extension = math.hypot(dx, dy)
    # Measure extension along the thumb, so tilting the hand does not shorten
    # an otherwise deliberate gesture. Its direction must still be upright.
    if extension <= 0.65 * scale or abs(dy) <= abs(dx) * 1.1:
        return None
    # A deliberate thumb is straight at its interphalangeal joint and clearly
    # projects beyond the folded fingers, rather than just pointing upward.
    proximal = [points[3][c] - points[2][c] for c in (0, 1)]
    distal = [points[4][c] - points[3][c] for c in (0, 1)]
    lengths = math.hypot(*proximal), math.hypot(*distal)
    if min(lengths) < scale * 0.12:
        return None
    if sum(a * b for a, b in zip(proximal, distal)) < 0.8 * lengths[0] * lengths[1]:
        return None
    clearance = min((points[4][0] - point[0]) * dx
                    + (points[4][1] - point[1]) * dy for point in points[5:])
    if clearance < 0.10 * scale * extension:
        return None
    return 'up' if dy < 0 else 'down'


def is_thumbs_up(points):
    return _thumb_direction(points) == 'up'


def is_thumbs_down(points):
    return _thumb_direction(points) == 'down'


def is_two_hand_heart(a, b):
    if not _valid(a) or not _valid(b):
        return False
    scale = (_distance(a[5], a[17]) + _distance(b[5], b[17])) / 2
    # Both index fingertips meet at the top and both thumb tips meet below.
    # A little separation is allowed for imperfect tracking and curved fingers.
    if _distance(a[8], b[8]) > 0.9 * scale or _distance(a[4], b[4]) > 0.9 * scale:
        return False
    for points in (a, b):
        if points[8][1] >= points[4][1] - 0.15 * scale:
            return False
        if _distance(points[8], points[4]) < 0.35 * scale:
            return False
        if sum(_curled(points, pip, tip) for pip, tip in ((10, 12), (14, 16), (18, 20))) < 2:
            return False
    return True


def classify(hands):
    def same_hand(a, b):
        center_a = [(a[0][c] + a[9][c]) / 2 for c in (0, 1)]
        center_b = [(b[0][c] + b[9][c]) / 2 for c in (0, 1)]
        scale = (_distance(a[5], a[17]) + _distance(b[5], b[17])) / 2
        rms = math.sqrt(sum(_distance(x, y) ** 2 for x, y in zip(a, b)) / 21)
        return _distance(center_a, center_b) < 0.4 * scale and rms < 0.22 * scale

    unique = []
    for hand in hands:
        if not _valid(hand):
            continue
        # Tracking can briefly report the same hand twice. Such a duplicate
        # must not turn one thumb into fireworks or one V into confetti.
        if any(same_hand(hand, other) for other in unique):
            continue
        unique.append(hand)
    hands = unique
    if any(is_two_hand_heart(a, b) for a, b in combinations(hands, 2)):
        return 'heart'
    if any(is_salute(hand) for hand in hands):
        return 'prosper'
    poses = []
    for hand in hands:
        direction = _thumb_direction(hand)
        if direction:
            poses.append('thumbs_' + direction)
        elif is_peace(hand):
            poses.append('peace')
        elif is_horns(hand):
            poses.append('horns')
    # Resolve two-hand effects before their single-hand versions. A single
    # horns gesture does not fire: Apple's laser gesture requires both hands.
    for pose, reaction in (('thumbs_up', 'fireworks'), ('thumbs_down', 'rain'),
                           ('peace', 'confetti'), ('horns', 'lasers')):
        if poses.count(pose) >= 2:
            return reaction
    if len(poses) == 1:
        return {'thumbs_up': 'thumbs_up', 'thumbs_down': 'thumbs_down',
                'peace': 'balloons'}.get(poses[0])
    return None


def _finger_pattern(landmarks, pattern, *, folded_ratio=1.02):
    if not _valid(landmarks):
        return False

    wrist = landmarks[0]
    scale = _distance(landmarks[5], landmarks[17])

    def finger(mcp, pip, tip, extended):
        a, b, c = landmarks[mcp], landmarks[pip], landmarks[tip]
        u, v = (a[0] - b[0], a[1] - b[1]), (c[0] - b[0], c[1] - b[1])
        norm = math.hypot(*u) * math.hypot(*v)
        if norm < scale * scale * 0.005:
            return False
        cosine = max(-1.0, min(1.0, (u[0] * v[0] + u[1] * v[1]) / norm))
        angle = math.degrees(math.acos(cosine))
        ratio = _distance(c, wrist) / max(_distance(b, wrist), scale * 0.1)
        if extended:
            return angle > 145 and ratio > 1.07
        return angle < 155 and ratio < folded_ratio

    return all(
        finger(mcp, pip, tip, extended)
        for (mcp, pip, tip), extended in zip(
            ((5, 6, 8), (9, 10, 12), (13, 14, 16), (17, 18, 20)), pattern)
    )


def is_horns(landmarks):
    """Index and pinky extended, middle/ring folded; thumb unrestricted."""
    return _finger_pattern(landmarks, (True, False, False, True))


def is_peace(landmarks):
    """Index and middle extended and spread apart; ring/pinky folded."""
    if not _finger_pattern(landmarks, (True, True, False, False)):
        return False
    scale = _distance(landmarks[5], landmarks[17])
    return _distance(landmarks[8], landmarks[12]) > scale * 0.25


def is_salute(points):
    if not _finger_pattern(points, (True, True, True, True)):
        return False
    scale = _distance(points[5], points[17])
    across = [(points[17][c] - points[5][c]) / scale for c in (0, 1)]

    def separation(a, b):
        return abs(sum((points[b][c] - points[a][c]) * across[c] for c in (0, 1)))

    gap = separation(12, 16)
    if gap < 0.48 * scale:
        return False
    if any(separation(a, b) > min(0.42 * scale, 0.68 * gap)
           for a, b in ((8, 12), (16, 20))):
        return False
    return (_distance(points[4], points[5]) > 0.6 * scale
            and _distance(points[4], points[0]) > 1.05 * _distance(points[3], points[0]))


def reaction_anchor(reaction, hands, aspect=1.0):
    """Position localized effects near the gesture; full-frame effects stay put."""
    if reaction == 'heart' and len(hands) >= 2:
        for a, b in combinations(hands, 2):
            if is_two_hand_heart(a, b):
                return ((a[4][0] + b[4][0]) / (2 * aspect),
                        (a[4][1] + b[4][1]) / 2)
    if reaction in ('thumbs_up', 'thumbs_down'):
        check = is_thumbs_up if reaction == 'thumbs_up' else is_thumbs_down
        for hand in hands:
            if check(hand):
                x = (hand[0][0] + hand[5][0]) / (2 * aspect)
                minimum_y = 0.32 if reaction == 'thumbs_up' else 0.2
                y = max(minimum_y, min(0.6, (hand[4][1] + hand[0][1]) / 2 - 0.12))
                return (0.76 if x < 0.5 else 0.24, y)
    return None


@dataclass
class ReactionTrigger:
    hold: float = 0.45
    single_hold: float = 0.85
    cooldown: float = 7.0
    release: float = 0.4
    held_since: float | None = None
    released_since: float | None = None
    last_fired: float = -math.inf
    armed: bool = True
    held_gesture: str | None = None
    last_seen: float = -math.inf
    last_update: float = -math.inf
    last_reaction: str | None = None
    samples: int = 0
    dropout_grace: float = 0.22
    require_release: bool = False

    def reset_candidate(self):
        self.held_since = None
        self.held_gesture = None
        self.samples = 0

    def suppress(self, now, reaction=None, cooldown=True):
        self.reset_candidate()
        self.last_fired = now if cooldown else now - self.cooldown
        self.last_reaction = reaction
        self.require_release = True
        self.armed = False
        self.released_since = None

    def progress(self, now):
        if not self.held_gesture or self.held_since is None:
            return 0.0
        required = self.single_hold if self.held_gesture in ('thumbs_up', 'thumbs_down', 'balloons', 'prosper') else self.hold
        return min(1.0, max(0, (min(now, self.last_seen) - self.held_since) / required))

    def update(self, gesture, now):
        if now - self.last_update > 0.4:
            self.reset_candidate()
        self.last_update = now
        if not gesture:
            if now - self.last_seen > self.dropout_grace:
                self.reset_candidate()
            if self.released_since is None:
                self.released_since = now
            if now - self.released_since >= self.release:
                self.armed = True
                self.require_release = False
            return None
        self.released_since = None
        if self.held_since is None or self.held_gesture != gesture:
            self.held_since = now
            self.held_gesture = gesture
            self.samples = 0
        self.samples += 1
        self.last_seen = now
        # Leave a short grace period to bring the second hand into view, so
        # fireworks/confetti/rain are not preempted by a single-hand reaction.
        required_hold = self.single_hold if gesture in ('thumbs_up', 'thumbs_down', 'balloons', 'prosper') else self.hold
        eligible = self.armed or (gesture != self.last_reaction and not self.require_release)
        if (eligible and not self.require_release and self.samples >= 3
                and now - self.held_since >= required_hold
                and now - self.last_fired >= self.cooldown):
            self.last_fired = now
            self.armed = False
            self.last_reaction = gesture
            return gesture
        return None
