"""颜色数量与色相集合。

专利用差异函数 P(h) = ΔE(h) / δ(h)，并让相邻色相之间 P 的积分相等。
论文把捕获色相曲线的局部变化写成 G，并从最稳的青色 H=180 起积。
这里把二者合成：分子用论文的相邻色相差，分母用专利的标准差；
积分起点固定在 180°。没有实测曲线时，编码直接使用历史 64 色表。
"""

from __future__ import annotations

import math

import numpy as np

from miracode.palette import POWER_OF_TWO, measured_palette


def performance_index(delta_e: np.ndarray, sigma: np.ndarray, floor: float = 1e-3) -> np.ndarray:
    """P(h) = ΔE(h) / δ(h)。δ 过小的色相抬到 floor，避免除零。"""

    delta = np.asarray(delta_e, dtype=float)
    scale = np.maximum(np.asarray(sigma, dtype=float), floor)
    if delta.shape != (360,) or scale.shape != (360,):
        raise ValueError("ΔE 和 δ 都应为长度 360 的色相曲线")
    if np.any(delta < 0):
        raise ValueError("ΔE 不能为负")
    return delta / scale


def performance_from_capture(mean_hue: np.ndarray, sigma: np.ndarray) -> np.ndarray:
    """由实拍均值曲线 E(h) 和标准差 δ(h) 得到差异函数。

    ΔE(h) 取 E(h+1) 与 E(h-1) 的圆周距离，对应论文里的 |G(h)|。
    实测曲线单调时，它与论文不取绝对值的 G 一致，同时保证积分可逆。
    """

    mean = np.asarray(mean_hue, dtype=float) % 360.0
    if mean.shape != (360,):
        raise ValueError("均值曲线长度应为 360")
    delta = np.empty(360, dtype=float)
    for hue in range(360):
        diff = mean[(hue + 1) % 360] - mean[(hue - 1) % 360]
        delta[hue] = abs((diff + 180.0) % 360.0 - 180.0)
    return performance_index(delta, sigma)


def _walk(performance: np.ndarray, anchor: float) -> tuple[int, np.ndarray, np.ndarray, float]:
    curve = np.asarray(performance, dtype=float)
    if curve.shape != (360,):
        raise ValueError("差异函数长度应为 360")
    if np.any(curve < 0) or float(curve.sum()) <= 0:
        raise ValueError("差异函数必须非负且不能全为零")
    anchor_i = int(round(anchor)) % 360
    path = np.array([(anchor_i + step) % 360 for step in range(360)], dtype=int)
    cumulative = np.cumsum(curve[path])
    return anchor_i, path, cumulative, float(cumulative[-1])


def _invert(cumulative: np.ndarray, path: np.ndarray, anchor_i: int, target: float, total: float) -> float:
    if target <= 0.0 or target >= total:
        return float(anchor_i)
    index = int(np.searchsorted(cumulative, target, side="left"))
    index = min(max(index, 0), 359)
    previous = 0.0 if index == 0 else float(cumulative[index - 1])
    span = float(cumulative[index]) - previous
    fraction = 0.0 if span <= 0 else (target - previous) / span
    return float((int(path[index]) + fraction) % 360.0)


def select_hues(performance: np.ndarray, n: int, anchor: float = 180.0) -> np.ndarray:
    """选出 n 个编码色相，使相邻色相之间 P 的积分相等。第一个色相在 anchor。"""

    if n < 2:
        raise ValueError("至少需要 2 种颜色")
    anchor_i, path, cumulative, total = _walk(performance, anchor)
    return np.array(
        [_invert(cumulative, path, anchor_i, i * total / n, total) for i in range(n)],
        dtype=float,
    )


def select_bounds(performance: np.ndarray, n: int, anchor: float = 180.0) -> np.ndarray:
    """色板判定色相。每个边界把相邻编码色之间的 P 积分再分成相等的两段。"""

    anchor_i, path, cumulative, total = _walk(performance, anchor)
    return np.array(
        [_invert(cumulative, path, anchor_i, (i + 0.5) * total / n, total) for i in range(n)],
        dtype=float,
    )


def gross_capacity_bytes(n: int, accuracy: float, blocks: int, symbol_bits: int = 8) -> float:
    """一帧在给定识别率下还能可靠传输的字节数。

    与历史 ``capacity.m`` 同一形式::

        (2 * p^(b / log2(n)) - 1) * m * log2(n) / b

    ``accuracy`` 是 0 到 1 的色块识别率 p。结果为负表示校验位盖不住误码。
    """

    if n < 2 or blocks <= 0:
        raise ValueError("颜色数和色块数必须为正")
    bits = math.log2(n)
    rate = 2.0 * (accuracy ** (symbol_bits / bits)) - 1.0
    return rate * blocks * bits / symbol_bits


def choose_color_count(accuracy_by_n: dict[int, float], blocks: int = 1888) -> int:
    """在 2 的幂里选容量最大的颜色数。容量为负的档位弃用。"""

    best_n = None
    best_capacity = -1.0
    for n, accuracy in accuracy_by_n.items():
        if n not in POWER_OF_TWO:
            continue
        capacity = gross_capacity_bytes(n, accuracy, blocks)
        if capacity > best_capacity:
            best_capacity = capacity
            best_n = n
    if best_n is None:
        raise ValueError("没有可用的颜色数量")
    return best_n


class ColorSelector:
    """按差异函数选色。没有曲线时退回实测 64 色表。"""

    def __init__(self, performance: np.ndarray | None = None) -> None:
        self.performance = performance

    def palette(self, n: int) -> tuple[np.ndarray, np.ndarray]:
        if self.performance is None:
            return measured_palette(n)
        return select_hues(self.performance, n), select_bounds(self.performance, n)

    @staticmethod
    def hues(performance: np.ndarray, n: int, anchor: float = 180.0) -> np.ndarray:
        return select_hues(performance, n, anchor)

    @staticmethod
    def bounds(performance: np.ndarray, n: int, anchor: float = 180.0) -> np.ndarray:
        return select_bounds(performance, n, anchor)

    @staticmethod
    def from_capture(mean_hue: np.ndarray, sigma: np.ndarray) -> np.ndarray:
        return performance_from_capture(mean_hue, sigma)

    @staticmethod
    def index(delta_e: np.ndarray, sigma: np.ndarray, floor: float = 1e-3) -> np.ndarray:
        return performance_index(delta_e, sigma, floor)

    @staticmethod
    def capacity(n: int, accuracy: float, blocks: int, symbol_bits: int = 8) -> float:
        return gross_capacity_bytes(n, accuracy, blocks, symbol_bits)

    @staticmethod
    def choose(accuracy_by_n: dict[int, float], blocks: int = 1888) -> int:
        return choose_color_count(accuracy_by_n, blocks)
