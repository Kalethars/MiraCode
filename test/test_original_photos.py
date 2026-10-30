"""在原始实拍上检查色相稳定性和定位图案。"""

from __future__ import annotations

import unittest

import support
import numpy as np
from PIL import Image

from miracode.finder import find_finders
from miracode.palette import rgb_image_to_hsv
from miracode.photos import SourcePhotos

support

TARGET_AREA = 909312


def _downscale(image: Image.Image) -> np.ndarray:
    width, height = image.size
    partial = max((width * height / TARGET_AREA) ** 0.5, 1.0)
    resized = image.resize((max(1, round(width / partial)), max(1, round(height / partial))), Image.Resampling.BICUBIC)
    return np.asarray(resized)


def _mean_hue_and_value(path) -> tuple[float, float]:
    image = Image.open(path).convert("RGB")
    image.thumbnail((320, 320))
    hue, saturation, value = rgb_image_to_hsv(np.asarray(image))
    chosen = saturation > 0.4
    angles = np.deg2rad(hue[chosen])
    mean = np.rad2deg(np.arctan2(np.sin(angles).mean(), np.cos(angles).mean())) % 360.0
    return float(mean), float(value.mean())


def _circular_std(hues: np.ndarray) -> float:
    angles = np.deg2rad(hues)
    radius = float(np.hypot(np.sin(angles).mean(), np.cos(angles).mean()))
    return float(np.rad2deg(np.sqrt(max(0.0, -2.0 * np.log(max(radius, 1e-9))))))


class TestOriginalPhotos(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.photos = SourcePhotos.discover()

    def test_hue360_contains_the_analysed_captures(self) -> None:
        for index in range(1, 109):
            path = self.photos.hue_capture(index)
            self.assertGreater(path.stat().st_size, 500_000, msg=path.name)

    def test_hsv_burst_is_stabler_than_the_hue_sweep(self) -> None:
        hsv = [_mean_hue_and_value(path) for path in self.photos.stability_burst("Test_HSV")]
        sweep = [_mean_hue_and_value(path) for path in self.photos.stability_burst("Test_Hue")]
        self.assertGreaterEqual(len(hsv), 8)
        self.assertGreaterEqual(len(sweep), 8)
        hsv_std = _circular_std(np.array([item[0] for item in hsv]))
        sweep_std = _circular_std(np.array([item[0] for item in sweep]))
        self.assertLess(hsv_std, 10.0)
        self.assertGreater(sweep_std, hsv_std)

    def test_finder_runs_on_downscaled_captures(self) -> None:
        found = 0
        for index in (50, 80, 108):
            image = _downscale(Image.open(self.photos.hue_capture(index)).convert("RGB"))
            if len(find_finders(image)) >= 2:
                found += 1
        self.assertGreaterEqual(found, 2)
