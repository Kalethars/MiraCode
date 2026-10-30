"""色相选择、容量和历史色表。"""

from __future__ import annotations

import sys
import unittest

import support
import numpy as np

from miracode.codec import HueClassifier
from miracode.color_selection import ColorSelector
from miracode.palette import CODING16, HUE64, measured_palette

support  # 路径在 import 时已经插好


class TestRuntime(unittest.TestCase):
    def test_python_310(self) -> None:
        self.assertEqual(sys.version_info[:2], (3, 10))


class TestMeasuredPalette(unittest.TestCase):
    def test_hue64_length(self) -> None:
        self.assertEqual(len(HUE64), 64)

    def test_coding16_matches_historical_table(self) -> None:
        coding, _bounds = measured_palette(16)
        for got, expected in zip(coding, CODING16):
            self.assertAlmostEqual(float(got), expected, places=2)
        self.assertAlmostEqual(float(coding[8]), 180.0, places=2)

    def test_bounds_bracket_coding_hues(self) -> None:
        for n in (2, 4, 8, 16, 32, 64):
            coding, bounds = measured_palette(n)
            for index, hue in enumerate(coding):
                self.assertEqual(HueClassifier.classify(float(hue), bounds), index, msg=f"n={n} i={index}")


class TestSelection(unittest.TestCase):
    def test_constant_performance_is_uniform_from_cyan(self) -> None:
        hues = ColorSelector.hues(np.ones(360), 16, anchor=180)
        self.assertAlmostEqual(float(hues[0]), 180.0, delta=0.05)
        for index in range(16):
            expected = (180.0 + index * 22.5) % 360.0
            self.assertAlmostEqual(float(hues[index]), expected, delta=0.05)
        bounds = ColorSelector.bounds(np.ones(360), 16, anchor=180)
        self.assertAlmostEqual(float(bounds[0]), (180.0 + 11.25) % 360.0, delta=0.05)

    def test_high_performance_region_gets_tighter_spacing(self) -> None:
        curve = np.ones(360)
        curve[180:240] = 5.0
        hues = ColorSelector.hues(curve, 8, anchor=180)
        gap_near = (float(hues[1]) - float(hues[0])) % 360.0
        gap_far = (float(hues[5]) - float(hues[4])) % 360.0
        self.assertLess(gap_near, gap_far)

    def test_capture_curve_uses_sigma(self) -> None:
        mean = np.arange(360, dtype=float)
        sigma = np.ones(360)
        sigma[0] = 4.0
        curve = ColorSelector.from_capture(mean, sigma)
        # 恒等捕获曲线的相邻差约为 2，除以标准差后色相 0 的差异更小。
        self.assertAlmostEqual(float(curve[10]), 2.0, places=5)
        self.assertAlmostEqual(float(curve[0]), 0.5, places=5)


class TestCapacity(unittest.TestCase):
    def test_perfect_recognition_matches_capacity_script(self) -> None:
        # capacity.m：p=1、16 色、1888 块、8 比特符号 → 944 字节。
        self.assertAlmostEqual(ColorSelector.capacity(16, 1.0, 1888), 944.0, places=6)
        self.assertAlmostEqual(ColorSelector.capacity(4, 1.0, 1888), 472.0, places=6)

    def test_choose_sixteen_when_finer_palettes_collapse(self) -> None:
        accuracy = {2: 0.999, 4: 0.999, 8: 0.995, 16: 0.99, 32: 0.70, 64: 0.55}
        self.assertEqual(ColorSelector.choose(accuracy, blocks=1888), 16)
