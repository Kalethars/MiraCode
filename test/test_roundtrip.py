"""整帧编码、定位、色板识别和多帧拼接。"""

from __future__ import annotations

import subprocess
import sys
import unittest

import support
import numpy as np

from miracode.errors import MixedFrame
from miracode.pipeline import MiraCode

support


class TestFrame(unittest.TestCase):
    def test_alignment_is_black_white(self) -> None:
        link = MiraCode(16)
        image = link.encode(b"align")[0]
        polarity = link.alignment_polarity(image)
        self.assertEqual(polarity[0], True)
        self.assertEqual(polarity, [index % 2 == 0 for index in range(len(polarity))])

    def test_text_roundtrip(self) -> None:
        link = MiraCode(16)
        payload = "MiraCode 四维码".encode("utf-8")
        self.assertEqual(link.decode(link.encode(payload)), payload)

    def test_empty_payload(self) -> None:
        link = MiraCode(16)
        self.assertEqual(link.decode(link.encode(b"")), b"")

    def test_multiple_frames(self) -> None:
        link = MiraCode(16)
        limit = link.codec.payload_capacity(link.geometry.data_symbol_count)
        payload = bytes((i * 13) % 256 for i in range(limit + 80))
        frames = link.encode(payload)
        self.assertGreater(len(frames), 1)
        self.assertEqual(link.decode(frames), payload)

    def test_global_hue_shift_still_decodes(self) -> None:
        link = MiraCode(16)
        payload = b"palette tracks the shift"
        frames = [link.shift_hue(image, 12.0) for image in link.encode(payload)]
        self.assertEqual(link.decode(frames), payload)

    def test_rotation_keeps_orientation(self) -> None:
        link = MiraCode(16)
        payload = b"orientation"
        image = link.encode(payload)[0]
        for turns in (1, 2, 3):
            rotated = np.rot90(image, k=turns)
            self.assertEqual(link.decode_frame(rotated).payload, payload)

    def test_mixed_frame_is_rejected(self) -> None:
        link = MiraCode(16)
        even = link.encode(b"ab")[0]
        green = link.painter.render(
            link.codec.encode_data(b"cd", link.geometry.data_symbol_count),
            link.codec.encode_frame_info(2, 1, 2),
            link.coding_hues,
            link.bound_hues,
            frame_index=1,
        )
        with self.assertRaises(MixedFrame):
            link.decode_frame(MiraCode.blend(even, green))

    def test_eight_colors(self) -> None:
        link = MiraCode(8)
        payload = "八色".encode("utf-8")
        self.assertEqual(link.decode(link.encode(payload)), payload)

    def test_cli_roundtrip(self) -> None:
        completed = subprocess.run(
            [sys.executable, "-m", "miracode", "roundtrip", "--text", "cli"],
            cwd=support.ROOT,
            env={**dict(**{k: v for k, v in __import__("os").environ.items()}), "PYTHONPATH": str(support.SRC)},
            check=False,
            capture_output=True,
            text=True,
        )
        self.assertEqual(completed.returncode, 0, msg=completed.stderr)
        self.assertIn("cli", completed.stdout)
