"""发送端和接收端。外面只通过 MiraCode 这一条链路进出。"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from miracode.codec import HueClassifier, SymbolCodec
from miracode.color_selection import ColorSelector
from miracode.errors import DecodeError, MixedFrame
from miracode.finder import FrameLocator
from miracode.layout import FramePainter, Geometry
from miracode.palette import mean_hue, rgb_image_to_hsv


@dataclass
class DecodedFrame:
    index: int
    total: int
    payload: bytes


class MiraCode:
    """一次编解码会话：选定颜色数，生成帧，或从照片还原文件。"""

    def __init__(self, n_colors: int = 16, performance: np.ndarray | None = None) -> None:
        self.n_colors = n_colors
        self.selector = ColorSelector(performance)
        self.coding_hues, self.bound_hues = self.selector.palette(n_colors)
        self.geometry = Geometry.for_colors(n_colors)
        self.codec = SymbolCodec(n_colors)
        self.painter = FramePainter(self.geometry)
        self.locator = FrameLocator(self.geometry)

    def encode(self, payload: bytes) -> list[np.ndarray]:
        capacity = self.codec.payload_capacity(self.geometry.data_symbol_count)
        if len(payload) == 0:
            chunks = [b""]
        else:
            chunks = [payload[offset : offset + capacity] for offset in range(0, len(payload), capacity)]
        frames = []
        total = len(chunks)
        for index, chunk in enumerate(chunks):
            data_symbols = self.codec.encode_data(chunk, self.geometry.data_symbol_count)
            info_symbols = self.codec.encode_frame_info(total, index, len(chunk))
            frames.append(self.painter.render(data_symbols, info_symbols, self.coding_hues, self.bound_hues, index))
        return frames

    def decode_frame(self, image: np.ndarray) -> DecodedFrame:
        image = np.ascontiguousarray(image)
        transform, _corners = self.locator.locate(image)
        info_symbols = self._read_frame_info(image, transform)
        total, index, length = self.codec.decode_frame_info(info_symbols)
        bounds = self._read_palette(image, transform)
        symbols = self._read_data(image, transform, bounds)
        return DecodedFrame(index, total, self.codec.decode_data(symbols, length))

    def decode(self, frames: list[np.ndarray]) -> bytes:
        parts: dict[int, bytes] = {}
        total: int | None = None
        for image in frames:
            try:
                frame = self.decode_frame(image)
            except MixedFrame:
                continue
            if total is None:
                total = frame.total
            elif frame.total != total:
                raise DecodeError("各帧记录的总帧数不一致")
            parts[frame.index] = frame.payload
        if total is None:
            raise DecodeError("没有可解码的帧")
        missing = [index for index in range(total) if index not in parts]
        if missing:
            raise DecodeError(f"缺少帧 {missing}")
        return b"".join(parts[index] for index in range(total))

    def shift_hue(self, image: np.ndarray, degrees: float) -> np.ndarray:
        """模拟拍摄时的整体色相偏移。黑白定位参考线保持不变。"""

        hue, sat, val = rgb_image_to_hsv(image)
        move = (sat > 0.45) & (val > 0.2)
        hue = np.where(move, (hue + degrees) % 360.0, hue)
        h = hue / 60.0
        c = val * sat
        x = c * (1.0 - np.abs(h % 2.0 - 1.0))
        m = val - c
        sector = np.mod(h.astype(int), 6)
        rgb = np.zeros(image.shape, dtype=np.float32)
        choices = (
            (c, x, np.zeros_like(c)),
            (x, c, np.zeros_like(c)),
            (np.zeros_like(c), c, x),
            (np.zeros_like(c), x, c),
            (x, np.zeros_like(c), c),
            (c, np.zeros_like(c), x),
        )
        for index, channels in enumerate(choices):
            sel = sector == index
            for channel, plane in enumerate(channels):
                rgb[:, :, channel][sel] = plane[sel]
        rgb += m[:, :, None]
        return np.clip(np.round(rgb * 255.0), 0, 255).astype(np.uint8)

    @staticmethod
    def blend(left: np.ndarray, right: np.ndarray) -> np.ndarray:
        """两帧各占一半曝光，用来制造混叠照片。"""

        return ((left.astype(np.uint16) + right.astype(np.uint16)) // 2).astype(np.uint8)

    def alignment_polarity(self, image: np.ndarray) -> list[bool]:
        image = np.ascontiguousarray(image)
        transform, _corners = self.locator.locate(image)
        points = [
            self.geometry.module_center(self.geometry.data_x + col, self.geometry.top_align_y)
            for col in range(self.geometry.data_cols)
        ]
        mapped = self.locator.map_design(transform, np.array(points, dtype=float))
        polarity = []
        for x, y in mapped:
            patch = self.locator.sample(image, x, y, radius=2)
            polarity.append(bool(patch.mean() < 128))
        return polarity

    def _sample_hue(self, image: np.ndarray, x: float, y: float) -> float:
        return mean_hue(self.locator.sample(image, x, y, radius=3))

    def _read_palette(self, image: np.ndarray, transform: np.ndarray) -> np.ndarray:
        geom = self.geometry
        points = []
        owners = []
        for row in range(geom.data_rows):
            color_index = row % geom.n_colors
            for module_x in (geom.left_palette_x, geom.right_palette_x):
                points.append(geom.module_center(module_x, geom.data_y + row))
                owners.append(color_index)
        mapped = self.locator.map_design(transform, np.array(points, dtype=float))
        acc: dict[int, list[float]] = {index: [] for index in range(geom.n_colors)}
        for (x, y), owner in zip(mapped, owners):
            acc[owner].append(self._sample_hue(image, x, y))
        bounds = np.zeros(geom.n_colors, dtype=float)
        for index in range(geom.n_colors):
            if not acc[index]:
                raise DecodeError("色板不完整")
            angs = np.deg2rad(np.array(acc[index], dtype=float))
            bounds[index] = float(np.rad2deg(np.arctan2(np.sin(angs).mean(), np.cos(angs).mean())) % 360.0)
        return bounds

    def _read_data(self, image: np.ndarray, transform: np.ndarray, bounds: np.ndarray) -> list[int]:
        geom = self.geometry
        points = [
            geom.module_center(geom.data_x + col, geom.data_y + row)
            for row in range(geom.data_rows)
            for col in range(geom.data_cols)
        ]
        mapped = self.locator.map_design(transform, np.array(points, dtype=float))
        return [HueClassifier.classify(self._sample_hue(image, x, y), bounds) for x, y in mapped]

    def _read_frame_info(self, image: np.ndarray, transform: np.ndarray) -> list[int]:
        geom = self.geometry
        swatches = self.locator.map_design(
            transform,
            np.array([geom.module_center(0, geom.data_y + index) for index in range(4)], dtype=float),
        )
        hues = [self._sample_hue(image, x, y) for x, y in swatches]
        bounds = np.zeros(4, dtype=float)
        for index, hue in enumerate(hues):
            nxt = hues[(index + 1) % 4]
            bounds[index] = (hue + ((nxt - hue) % 360.0) / 2.0) % 360.0
        count = (SymbolCodec.INFO_PAYLOAD_BYTES + SymbolCodec.INFO_PARITY) * 4
        points = []
        for index in range(count):
            row, col = divmod(index, geom.info_cols)
            points.append(geom.module_center(geom.info_x + col, geom.data_y + row))
        mapped = self.locator.map_design(transform, np.array(points, dtype=float))
        return [HueClassifier.classify(self._sample_hue(image, x, y), bounds) for x, y in mapped]
