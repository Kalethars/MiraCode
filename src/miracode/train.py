"""用论文里的默认色相参数选择颜色数量。

这些参数来自实拍照片的汇总，已经整理成 JSON。
原始照片在单独的 Git LFS 仓库里，不参与这一步。
差异函数仍是专利里的 P = ΔE / δ。
"""

from __future__ import annotations

import json
import math
from pathlib import Path

import numpy as np

from miracode.color_selection import ColorSelector
from miracode.palette import POWER_OF_TWO


def default_parameters_path() -> Path:
    return Path(__file__).resolve().parent / "defaults" / "parameters.json"


def load_defaults(path: Path | None = None) -> dict:
    """读取规范化后的默认参数。四条色相曲线长度都是 360。"""

    document = json.loads((path or default_parameters_path()).read_text(encoding="utf-8"))
    curves = document["curves"]
    for name in ("captured_mean_hue", "difference", "std", "absolute_distance"):
        if len(curves[name]) != document["hue_count"]:
            raise ValueError(f"{name} 的长度与 hue_count 不一致")
    return document


def _curve(document: dict, name: str) -> np.ndarray:
    return np.asarray(document["curves"][name], dtype=float)


def _sector_half_width(bounds: np.ndarray, index: int) -> float:
    start = float(bounds[(index - 1) % len(bounds)])
    end = float(bounds[index])
    return (end - start) % 360.0 / 2.0


def _recognition_accuracy(coding: np.ndarray, bounds: np.ndarray, sigma: np.ndarray) -> float:
    """用色板半宽和该色相的标准差估计识别率。误差按正态分布。"""

    rates = []
    for index, hue in enumerate(coding):
        half = _sector_half_width(bounds, index)
        scale = max(float(sigma[int(round(hue)) % 360]), 1e-3)
        z = half / (scale * math.sqrt(2.0))
        rates.append(math.erf(z))
    return float(np.mean(rates))


class ColorModel:
    """由默认参数得到的一档颜色：数量、差异曲线、编码色和色板边界。"""

    def __init__(
        self,
        n_colors: int,
        performance: np.ndarray,
        coding_hues: np.ndarray,
        bounds: np.ndarray,
        accuracy_by_n: dict[int, float],
    ) -> None:
        self.n_colors = n_colors
        self.performance = performance
        self.coding_hues = coding_hues
        self.bounds = bounds
        self.accuracy_by_n = accuracy_by_n

    @classmethod
    def from_defaults(cls, path: Path | None = None, blocks: int = 1888) -> ColorModel:
        """用默认参数估计各档颜色数的识别率，选出容量最大的一档并生成色相。"""

        document = load_defaults(path)
        delta_e = np.abs(_curve(document, "difference"))
        sigma = np.maximum(_curve(document, "std"), 1e-3)
        performance = ColorSelector.index(delta_e, sigma)
        selector = ColorSelector(performance)
        accuracy = {n: _recognition_accuracy(*selector.palette(n), sigma) for n in POWER_OF_TWO}
        n_colors = selector.choose(accuracy, blocks=blocks)
        coding, bounds = selector.palette(n_colors)
        return cls(n_colors, performance, coding, bounds, accuracy)
