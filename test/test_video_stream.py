"""用历史实拍曲线训练，再把视频流编出来、读回来、解回去。"""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

import support
import numpy as np

from miracode.pipeline import MiraCode
from miracode.train import ColorModel, load_defaults
from miracode.video import AviVideo

support


class TestTrainingData(unittest.TestCase):
    def test_default_parameters_are_normalized(self) -> None:
        document = load_defaults()
        curves = document["curves"]
        for name in ("captured_mean_hue", "difference", "std", "absolute_distance"):
            self.assertEqual(len(curves[name]), 360)
        captured = curves["captured_mean_hue"]
        # 平均捕获色相从大约 4.5° 起，绕一圈回到 0° 附近。
        self.assertGreater(captured[0], 3.0)
        self.assertLess(captured[0], 8.0)
        self.assertLess(min(captured), 5.0)
        self.assertGreater(max(captured), 300.0)
        self.assertEqual(len(document["published_selection"]), 15)
        self.assertEqual(len(document["hsv_stability"]), 400)
        palette = document["palettes_by_color_count"]["15"]
        self.assertEqual(len(palette), 15)
        self.assertAlmostEqual(palette[0], document["published_selection"][0], places=2)

    def test_train_picks_a_power_of_two(self) -> None:
        model = ColorModel.from_defaults()
        self.assertIn(model.n_colors, (2, 4, 8, 16, 32, 64))
        self.assertEqual(len(model.coding_hues), model.n_colors)
        self.assertGreater(model.accuracy_by_n[model.n_colors], 0.5)


class TestVideoStream(unittest.TestCase):
    def test_train_encode_video_decode(self) -> None:
        model = ColorModel.from_defaults()
        link = MiraCode(model.n_colors, model.performance)
        payload = "MiraCode 训练后的视频流".encode("utf-8")
        frames = link.encode(payload)
        self.assertGreaterEqual(len(frames), 1)
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "miracode.avi"
            AviVideo(frames, fps=10).write(path)
            restored = AviVideo.read(path)
        self.assertEqual(len(restored.frames), len(frames))
        for original, restored_frame in zip(frames, restored.frames):
            self.assertTrue(np.array_equal(original, restored_frame))
        self.assertEqual(link.decode(restored.frames), payload)
