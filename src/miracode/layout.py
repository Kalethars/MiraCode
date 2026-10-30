"""彩色二维码版面。

几何把三边拼在一起：

- 专利：四角定位图案，其中一个更小，用来定方向；定位图案之间是黑白相间的
  定位参考线；纵向参考线外侧是按顺序排列的色板；帧信息单独放在一侧，只用 4 色。
- 论文和 ``createpic_chosen_new.m``：定位图案黑白宽度比 1:1:2:1:1，色块 16 像素。
- 专利的混叠检测：定位图案里的非黑色环在相邻帧之间红绿交替。
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from miracode.palette import FRAME_HUES, hue_to_rgb

MODULE = 16
FINDER_MODULES = 6
SPECIAL_FINDER_PX = 72
RED = np.array([255, 0, 0], dtype=np.uint8)
GREEN = np.array([0, 255, 0], dtype=np.uint8)


@dataclass(frozen=True)
class Geometry:
    n_colors: int
    module: int = MODULE
    margin: int = 1
    finder: int = FINDER_MODULES
    data_rows: int = 32
    data_cols: int = 24
    info_cols: int = 2

    @property
    def left_palette_x(self) -> int:
        return self.margin + self.finder

    @property
    def left_align_x(self) -> int:
        return self.left_palette_x + 1

    @property
    def info_x(self) -> int:
        return self.left_align_x + 1

    @property
    def data_x(self) -> int:
        return self.info_x + self.info_cols

    @property
    def right_align_x(self) -> int:
        return self.data_x + self.data_cols

    @property
    def right_palette_x(self) -> int:
        return self.right_align_x + 1

    @property
    def right_finder_x(self) -> int:
        return self.right_palette_x + 1

    @property
    def top_align_y(self) -> int:
        return self.margin + self.finder

    @property
    def data_y(self) -> int:
        return self.top_align_y + 1

    @property
    def bottom_align_y(self) -> int:
        return self.data_y + self.data_rows

    @property
    def bottom_finder_y(self) -> int:
        return self.bottom_align_y + 1

    @property
    def width_modules(self) -> int:
        return self.right_finder_x + self.finder + self.margin

    @property
    def height_modules(self) -> int:
        return self.bottom_finder_y + self.finder + self.margin

    @property
    def data_symbol_count(self) -> int:
        return self.data_rows * self.data_cols

    def pixel_box(self, module_x: int, module_y: int) -> tuple[int, int, int, int]:
        m = self.module
        return module_y * m, module_y * m + m, module_x * m, module_x * m + m

    def module_center(self, module_x: int, module_y: int) -> tuple[float, float]:
        m = self.module
        return (module_x + 0.5) * m, (module_y + 0.5) * m

    def finder_center(self, slot_x: int, slot_y: int) -> tuple[float, float]:
        m = self.module
        origin_x = slot_x * m
        origin_y = slot_y * m
        side = self.finder * m
        return origin_x + side / 2.0, origin_y + side / 2.0

    def design_corners(self) -> np.ndarray:
        """TL, TR, BR, BL 的中心，坐标为 (x, y)。"""

        tl = self.finder_center(self.margin, self.margin)
        tr = self.finder_center(self.right_finder_x, self.margin)
        br = self.finder_center(self.right_finder_x, self.bottom_finder_y)
        bl = self.finder_center(self.margin, self.bottom_finder_y)
        return np.array([tl, tr, br, bl], dtype=float)

    @classmethod
    def for_colors(cls, n_colors: int) -> Geometry:
        """色板要盖住每一种颜色，所以行数不小于颜色数，并且取 32 的倍数档。"""

        rows = 64 if n_colors > 32 else 32
        return cls(n_colors=n_colors, data_rows=rows)


def _fill(image: np.ndarray, y0: int, y1: int, x0: int, x1: int, color: np.ndarray) -> None:
    image[y0:y1, x0:x1] = color


def _fill_module(image: np.ndarray, geom: Geometry, module_x: int, module_y: int, color: np.ndarray) -> None:
    y0, y1, x0, x1 = geom.pixel_box(module_x, module_y)
    _fill(image, y0, y1, x0, x1, color)


def _draw_finder(image: np.ndarray, x: int, y: int, side: int, ring: np.ndarray) -> None:
    """在 (x, y) 画边长 side 的 1:1:2:1:1 定位图案，非黑色环用 ring。"""

    black = np.zeros(3, dtype=np.uint8)
    _fill(image, y, y + side, x, x + side, black)
    unit = side // 6
    _fill(image, y + unit, y + side - unit, x + unit, x + side - unit, ring)
    inner = 2 * unit
    _fill(image, y + inner, y + side - inner, x + inner, x + side - inner, black)


class FramePainter:
    """按版面把符号画成一帧。偶数帧定位环为红，奇数帧为绿。"""

    def __init__(self, geometry: Geometry) -> None:
        self.geometry = geometry

    def render(
        self,
        data_symbols: list[int],
        info_symbols: list[int],
        coding_hues: np.ndarray,
        bound_hues: np.ndarray,
        frame_index: int,
    ) -> np.ndarray:
        geom = self.geometry
        if len(data_symbols) != geom.data_symbol_count:
            raise ValueError("数据符号数量与版面不一致")
        image = np.full((geom.height_modules * geom.module, geom.width_modules * geom.module, 3), 255, dtype=np.uint8)
        ring = RED if frame_index % 2 == 0 else GREEN
        normal = geom.finder * geom.module
        special = SPECIAL_FINDER_PX
        offset = (normal - special) // 2

        slots = (
            (geom.margin, geom.margin, True),
            (geom.right_finder_x, geom.margin, False),
            (geom.margin, geom.bottom_finder_y, False),
            (geom.right_finder_x, geom.bottom_finder_y, False),
        )
        for module_x, module_y, is_special in slots:
            px = module_x * geom.module
            py = module_y * geom.module
            if is_special:
                _draw_finder(image, px + offset, py + offset, special, ring)
            else:
                _draw_finder(image, px, py, normal, ring)

        black = np.zeros(3, dtype=np.uint8)
        white = np.array([255, 255, 255], dtype=np.uint8)
        for col in range(geom.data_cols):
            color = black if col % 2 == 0 else white
            _fill_module(image, geom, geom.data_x + col, geom.top_align_y, color)
            _fill_module(image, geom, geom.data_x + col, geom.bottom_align_y, color)
        for row in range(geom.data_rows):
            color = black if row % 2 == 0 else white
            _fill_module(image, geom, geom.left_align_x, geom.data_y + row, color)
            _fill_module(image, geom, geom.right_align_x, geom.data_y + row, color)

        for row in range(geom.data_rows):
            color = hue_to_rgb(float(bound_hues[row % len(bound_hues)]))
            _fill_module(image, geom, geom.left_palette_x, geom.data_y + row, color)
            _fill_module(image, geom, geom.right_palette_x, geom.data_y + row, color)

        for index, hue in enumerate(FRAME_HUES):
            _fill_module(image, geom, 0, geom.data_y + index, hue_to_rgb(hue))

        for index, symbol in enumerate(info_symbols):
            row, col = divmod(index, geom.info_cols)
            _fill_module(image, geom, geom.info_x + col, geom.data_y + row, hue_to_rgb(FRAME_HUES[symbol]))

        for index, symbol in enumerate(data_symbols):
            row, col = divmod(index, geom.data_cols)
            _fill_module(image, geom, geom.data_x + col, geom.data_y + row, hue_to_rgb(float(coding_hues[symbol])))
        return image
