import math
import random
import unittest

from gestures import (ReactionTrigger, classify, is_horns, is_peace, is_salute,
                      is_thumbs_up, is_thumbs_down, is_two_hand_heart, reaction_anchor)


def hand(extended=(True, False, False, True)):
    points = [[0.5, 0.75] for _ in range(21)]
    points[0] = [0.5, 0.9]
    for i, (x, straight) in enumerate(zip((0.35, 0.45, 0.55, 0.65), extended)):
        base = 5 + 4 * i
        points[base] = [x, 0.65]
        points[base + 1] = [x, 0.5]
        points[base + 2] = [x, 0.38 if straight else 0.59]
        points[base + 3] = [x, 0.28 if straight else 0.7]
    return points


def thumbs_up():
    points = hand((False, False, False, False))
    points[2], points[3], points[4] = [0.25, 0.7], [0.22, 0.55], [0.2, 0.35]
    return points


def side_on_thumb():
    return [[x, y] for x, y in (
        (0.50, 0.85), (0.45, 0.76), (0.42, 0.69), (0.40, 0.52), (0.39, 0.33),
        (0.47, 0.59), (0.58, 0.53), (0.60, 0.59), (0.51, 0.63),
        (0.55, 0.61), (0.67, 0.56), (0.67, 0.65), (0.55, 0.69),
        (0.60, 0.65), (0.72, 0.62), (0.71, 0.70), (0.58, 0.74),
        (0.64, 0.70), (0.73, 0.69), (0.71, 0.76), (0.62, 0.78),
    )]


def compact_thumb():
    points = thumbs_up()
    points[2], points[3], points[4] = [0.28, 0.68], [0.27, 0.575], [0.26, 0.47]
    return points


def salute():
    points = hand((True, True, True, True))
    points[2], points[3], points[4] = [0.25, 0.65], [0.19, 0.59], [0.12, 0.53]
    for index, tip in ((8, [0.32, 0.28]), (12, [0.38, 0.23]),
                       (16, [0.62, 0.26]), (20, [0.68, 0.33])):
        points[index] = tip
    return points


def heart_hands():
    a = hand((False, False, False, False))
    a[0] = [0.25, 0.8]
    a[5], a[6], a[8] = [0.35, 0.5], [0.4, 0.36], [0.49, 0.3]
    a[2], a[3], a[4] = [0.35, 0.65], [0.42, 0.55], [0.49, 0.5]
    for mcp, pip, tip in ((9, 10, 12), (13, 14, 16), (17, 18, 20)):
        a[mcp], a[pip], a[tip] = [0.25, 0.55], [0.22, 0.45], [0.25, 0.7]
    return a, [[1 - x, y] for x, y in a]


def pair(points):
    return ([[x * 0.5, y * 0.5] for x, y in points],
            [[x * 0.5 + 0.5, y * 0.5] for x, y in points])


class GestureTests(unittest.TestCase):
    def test_salute_pairs_remain_distinct_when_rotated_or_mirrored(self):
        for sign in (-1, 1):
            for angle in (0, 0.6, 1.8, math.pi):
                c, s = math.cos(angle), math.sin(angle)
                points = [[sign * x * c - y * s, sign * x * s + y * c] for x, y in salute()]
                with self.subTest(sign=sign, angle=angle):
                    self.assertTrue(is_salute(points))
                    self.assertEqual(classify([points]), 'prosper')

    def test_open_palms_wide_fingers_and_folded_thumb_are_not_salutes(self):
        wide = salute()
        for index, x in ((8, 0.1), (12, 0.35), (16, 0.6), (20, 0.85)):
            wide[index] = [x, 0.28]
        folded = salute()
        folded[4] = folded[5][:]
        bent = salute()
        bent[20] = [0.65, 0.7]
        for points in (hand((True, True, True, True)), wide, folded, bent, [], thumbs_up()):
            self.assertFalse(is_salute(points))
            self.assertNotEqual(classify([points]), 'prosper')

    def test_salute_needs_a_deliberate_single_hand_hold(self):
        trigger = ReactionTrigger()
        for t in (0, 0.2, 0.4, 0.6, 0.8):
            self.assertIsNone(trigger.update('prosper', t))
        self.assertEqual(trigger.update('prosper', 0.9), 'prosper')
        self.assertIsNone(trigger.update('prosper', 2))

    def test_salute_tolerates_a_shorter_pinky_without_widening_its_pair(self):
        points = salute()
        points[20] = [0.68, 0.4]
        self.assertTrue(is_salute(points))

    def test_all_eight_documented_mappings(self):
        up = thumbs_up()
        down = [[1 - x, 1 - y] for x, y in up]
        peace = hand((True, True, False, False))
        cases = [
            (heart_hands(), 'heart'), ([up], 'thumbs_up'), ([down], 'thumbs_down'),
            ([peace], 'balloons'), (pair(up), 'fireworks'), (pair(down), 'rain'),
            (pair(peace), 'confetti'), (pair(hand()), 'lasers'),
        ]
        for hands, reaction in cases:
            with self.subTest(reaction=reaction):
                self.assertEqual(classify(hands), reaction)
                self.assertEqual(classify(list(reversed(hands))), reaction)
                self.assertEqual(classify([[[1 - x, y] for x, y in points] for points in hands]), reaction)

    def test_single_horns_does_not_fire_lasers(self):
        self.assertIsNone(classify([hand()]))
        self.assertEqual(classify(pair(hand())), 'lasers')

    def test_mixed_gestures_and_open_palms_do_not_fire(self):
        up = thumbs_up()
        down = [[1 - x, 1 - y] for x, y in up]
        self.assertIsNone(classify([up, down]))
        self.assertIsNone(classify([up, hand((True, True, False, False))]))
        self.assertIsNone(classify(pair(hand((True, True, True, True)))))
        self.assertIsNone(classify([]))

    def test_down_direction_and_peace_spread(self):
        self.assertTrue(is_thumbs_down([[1 - x, 1 - y] for x, y in thumbs_up()]))
        self.assertFalse(is_thumbs_down(thumbs_up()))
        peace = hand((True, True, False, False))
        self.assertTrue(is_peace(peace))
        peace[12] = peace[8][:]
        self.assertFalse(is_peace(peace))

    def test_two_hand_grace_period(self):
        trigger = ReactionTrigger()
        self.assertIsNone(trigger.update('thumbs_up', 0))
        self.assertIsNone(trigger.update('thumbs_up', 0.6))
        self.assertIsNone(trigger.update('fireworks', 0.7))
        self.assertIsNone(trigger.update('fireworks', 0.9))
        self.assertEqual(trigger.update('fireworks', 1.2), 'fireworks')
        single = ReactionTrigger()
        self.assertIsNone(single.update('balloons', 0))
        self.assertIsNone(single.update('balloons', 0.3))
        self.assertIsNone(single.update('balloons', 0.6))
        self.assertIsNone(single.update('balloons', 0.7))
        self.assertEqual(single.update('balloons', 0.9), 'balloons')

    def test_localized_reaction_anchors(self):
        a, b = heart_hands()
        self.assertEqual(reaction_anchor('heart', [a, b]), (0.5, 0.5))
        aspect = 16 / 9
        scaled = [[[x * aspect, y] for x, y in p] for p in (a, b)]
        self.assertEqual(reaction_anchor('heart', scaled, aspect), (0.5, 0.5))
        self.assertEqual(reaction_anchor('thumbs_up', [thumbs_up()])[0], 0.76)
        mirrored = [[1 - x, y] for x, y in thumbs_up()]
        self.assertEqual(reaction_anchor('thumbs_up', [mirrored])[0], 0.24)
        self.assertIsNone(reaction_anchor('fireworks', pair(thumbs_up())))

    def test_thumbs_up_and_mirrored_hand(self):
        points = thumbs_up()
        self.assertTrue(is_thumbs_up(points))
        self.assertTrue(is_thumbs_up([[1 - x, y] for x, y in points]))
        self.assertFalse(is_thumbs_up([[x, 1 - y] for x, y in points]))
        self.assertFalse(is_thumbs_up(hand((False, False, False, False))))
        self.assertEqual(classify([points]), 'thumbs_up')

    def test_deliberate_thumbs_survive_tilt_scale_and_mirroring(self):
        for sign in (-1, 1):
            for angle in (-0.4, 0, 0.4):
                for scale in (0.3, 1, 2):
                    c, s = math.cos(angle), math.sin(angle)
                    up = [[scale * (sign * x * c - y * s) + 0.2,
                           scale * (sign * x * s + y * c) - 0.1]
                          for x, y in thumbs_up()]
                    down = [[x, -y] for x, y in up]
                    with self.subTest(sign=sign, angle=angle, scale=scale):
                        self.assertEqual(classify([up]), 'thumbs_up')
                        self.assertEqual(classify([down]), 'thumbs_down')
                        self.assertEqual(classify(pair(up)), 'fireworks')
                        self.assertEqual(classify(pair(down)), 'rain')

    def test_side_on_closed_fist_has_a_clear_thumb(self):
        up = side_on_thumb()
        for points in (up, [[1 - x, y] for x, y in up]):
            self.assertEqual(classify([points]), 'thumbs_up')
            self.assertEqual(classify(pair(points)), 'fireworks')
            down = [[x, 1 - y] for x, y in points]
            self.assertEqual(classify([down]), 'thumbs_down')
            self.assertEqual(classify(pair(down)), 'rain')

    def test_natural_thumbs_tolerate_shorter_extension_and_relaxed_fingers(self):
        relaxed = side_on_thumb()
        relaxed[7], relaxed[8] = [0.70, 0.56], [0.76, 0.59]
        for name, pose in (('compact', compact_thumb()), ('relaxed', relaxed)):
            for mirror in (-1, 1):
                for angle in (-0.55, 0, 0.55):
                    for scale in (0.3, 1, 2):
                        c, s = math.cos(angle), math.sin(angle)
                        up = [[scale * (mirror * x * c - y * s) + 0.15,
                               scale * (mirror * x * s + y * c) - 0.1]
                              for x, y in pose]
                        down = [[x, -y] for x, y in up]
                        with self.subTest(pose=name, mirror=mirror, angle=angle, scale=scale):
                            self.assertEqual(classify([up]), 'thumbs_up')
                            self.assertEqual(classify([down]), 'thumbs_down')
                            self.assertEqual(classify(pair(up)), 'fireworks')
                            self.assertEqual(classify(pair(down)), 'rain')

    def test_outstretched_fingers_with_an_upright_thumb_do_not_trigger(self):
        pointing = side_on_thumb()
        pointing[7], pointing[8] = [0.69, 0.47], [0.80, 0.41]
        for pose in (hand((True, True, True, True)), pointing):
            pose[2], pose[3], pose[4] = [0.25, 0.7], [0.22, 0.55], [0.2, 0.35]
            for mirror in (-1, 1):
                up = [[mirror * x, y] for x, y in pose]
                down = [[x, 1 - y] for x, y in up]
                for points in (up, down):
                    self.assertIsNone(classify([points]))
                    self.assertIsNone(classify(pair(points)))

    def test_compact_thumbs_hold_through_small_tracking_jitter(self):
        rng = random.Random(1947)
        up = compact_thumb()
        down = [[x, 1 - y] for x, y in up]
        for hands, reaction, jitter in (([up], 'thumbs_up', 0.002),
                                       ([down], 'thumbs_down', 0.002),
                                       (pair(up), 'fireworks', 0.001),
                                       (pair(down), 'rain', 0.001)):
            with self.subTest(reaction=reaction):
                trigger = ReactionTrigger()
                fired = []
                for i in range(18):
                    sample = [[[x + rng.uniform(-jitter, jitter), y + rng.uniform(-jitter, jitter)]
                               for x, y in points] for points in hands]
                    detected = classify(sample)
                    self.assertEqual(detected, reaction)
                    result = trigger.update(detected, i / 8)
                    if result:
                        fired.append(result)
                self.assertEqual(fired, [reaction])

    def test_partial_and_bent_thumbs_do_not_form_reactions(self):
        cases = {
            'short_extension': {2: [0.25, 0.7], 3: [0.24, 0.63], 4: [0.23, 0.55]},
            'bent_joint': {2: [0.25, 0.7], 3: [0.15, 0.5], 4: [0.28, 0.32]},
            'inside_fist': {2: [0.25, 0.85], 3: [0.23, 0.675], 4: [0.21, 0.50]},
            'sideways': {2: [0.25, 0.7], 3: [0.11, 0.56], 4: [-0.03, 0.42]},
            'unfolded_finger': {6: [0.35, 0.77], 7: [0.35, 0.81], 8: [0.35, 0.85]},
        }
        for name, changes in cases.items():
            points = thumbs_up()
            for index, value in changes.items():
                points[index] = value
            for mirror in (False, True):
                up = [[1 - x if mirror else x, y] for x, y in points]
                down = [[x, 1 - y] for x, y in up]
                with self.subTest(pose=name, mirror=mirror):
                    self.assertFalse(is_thumbs_up(up))
                    self.assertFalse(is_thumbs_down(down))
                    self.assertIsNone(classify([up]))
                    for pose in (up, down):
                        self.assertIsNone(classify(pair(pose)))
                    trigger = ReactionTrigger()
                    self.assertTrue(all(trigger.update(classify([up]), i / 8) is None
                                        for i in range(25)))

    def test_heart_requires_two_meeting_hands(self):
        a, b = heart_hands()
        self.assertTrue(is_two_hand_heart(a, b))
        self.assertEqual(classify([a, b]), 'heart')
        self.assertIsNone(classify([a]))
        self.assertFalse(is_two_hand_heart(a, [[x + 0.4, y] for x, y in b]))
        self.assertFalse(is_two_hand_heart(thumbs_up(), thumbs_up()))
        open_hand = hand((True, True, True, True))
        self.assertFalse(is_two_hand_heart(open_hand, open_hand))

    def test_reaction_switch_restarts_hold(self):
        trigger = ReactionTrigger()
        self.assertIsNone(trigger.update('lasers', 0))
        self.assertIsNone(trigger.update('thumbs_up', 0.4))
        self.assertIsNone(trigger.update('heart', 0.8))
        self.assertIsNone(trigger.update('heart', 1.0))
        self.assertIsNone(trigger.update('heart', 1.2))
        self.assertEqual(trigger.update('heart', 1.3), 'heart')

    def test_horns_both_hands_rotated_and_scaled(self):
        for sign in (-1, 1):
            for angle in (0, 0.7, 1.7, math.pi):
                for scale in (0.4, 1.0, 1.8):
                    with self.subTest(sign=sign, angle=angle, scale=scale):
                        c, s = math.cos(angle), math.sin(angle)
                        transformed = [
                            [scale * (sign * x * c - y * s),
                             scale * (sign * x * s + y * c)] for x, y in hand()
                        ]
                        self.assertTrue(is_horns(transformed))

    def test_other_finger_patterns_do_not_trigger(self):
        for mask in range(16):
            extended = tuple(bool(mask & (1 << i)) for i in range(4))
            with self.subTest(extended=extended):
                self.assertEqual(is_horns(hand(extended)), extended == (True, False, False, True))

    def test_invalid_landmarks(self):
        self.assertFalse(is_horns([]))
        self.assertFalse(is_horns([[0, 0]] * 21))
        invalid = hand()
        invalid[8][0] = math.nan
        self.assertFalse(is_horns(invalid))
        self.assertFalse(is_horns([[] for _ in range(21)]))
        self.assertIsNone(classify([invalid]))

    def test_hold_release_and_cooldown(self):
        trigger = ReactionTrigger()
        self.assertIsNone(trigger.update('lasers', 0))
        self.assertIsNone(trigger.update('lasers', 0.2))
        self.assertEqual(trigger.update('lasers', 0.5), 'lasers')
        self.assertIsNone(trigger.update('lasers', 12))  # holding never repeats
        self.assertIsNone(trigger.update(None, 12.1))
        self.assertIsNone(trigger.update(None, 12.6))
        self.assertIsNone(trigger.update('lasers', 12.7))
        self.assertIsNone(trigger.update('lasers', 12.9))
        self.assertEqual(trigger.update('lasers', 13.2), 'lasers')
        trigger.update(None, 13.3)
        trigger.update(None, 13.8)
        trigger.update('lasers', 14)
        self.assertIsNone(trigger.update('lasers', 14.6))  # cooldown still applies

    def test_brief_detection_does_not_trigger(self):
        trigger = ReactionTrigger()
        self.assertIsNone(trigger.update('lasers', 0))
        self.assertIsNone(trigger.update(None, 0.3))
        self.assertIsNone(trigger.update('lasers', 0.4))
        self.assertIsNone(trigger.update('lasers', 0.6))

    def test_short_tracking_dropout_keeps_the_hold(self):
        trigger = ReactionTrigger()
        self.assertIsNone(trigger.update('lasers', 0))
        self.assertIsNone(trigger.update('lasers', 0.15))
        self.assertIsNone(trigger.update(None, 0.3))
        self.assertEqual(trigger.update('lasers', 0.5), 'lasers')

    def test_stale_observations_do_not_count_as_a_hold(self):
        trigger = ReactionTrigger()
        trigger.update('lasers', 0)
        trigger.update('lasers', 0.1)
        self.assertIsNone(trigger.update('lasers', 2))
        self.assertLess(trigger.progress(2), 0.01)

    def test_different_gesture_can_fire_without_a_blank_frame(self):
        trigger = ReactionTrigger(cooldown=1)
        for t in (0, 0.2, 0.5):
            first = trigger.update('lasers', t)
        self.assertEqual(first, 'lasers')
        for t in (0.7, 1.0, 1.3):
            self.assertIsNone(trigger.update('heart', t))
        self.assertEqual(trigger.update('heart', 1.6), 'heart')

    def test_manual_effect_waits_for_hand_release(self):
        trigger = ReactionTrigger(cooldown=1)
        trigger.suppress(0, 'lasers')
        for i in range(1, 21):
            self.assertIsNone(trigger.update('thumbs_up', i * 0.1))
        trigger.update(None, 2.1)
        trigger.update(None, 2.3)
        trigger.update(None, 2.6)
        for t in (2.7, 3, 3.3, 3.6):
            result = trigger.update('thumbs_up', t)
        self.assertEqual(result, 'thumbs_up')

    def test_duplicate_tracks_never_form_a_two_hand_effect(self):
        up = thumbs_up()
        duplicate = [[x + 0.002, y - 0.002] for x, y in up]
        self.assertEqual(classify([up, duplicate]), 'thumbs_up')
        peace = hand((True, True, False, False))
        self.assertEqual(classify([peace, peace]), 'balloons')
        self.assertIsNone(classify([hand(), hand()]))


if __name__ == '__main__':
    unittest.main()
