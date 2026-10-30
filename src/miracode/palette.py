"""实测色相表与 HSV 转换。

色相表来自历史代码 ``ColorMapping.java`` / ``createpic_chosen_new.m``。
那是室内与夜间实拍后，按可区分度挑出来的 64 个色相，不是色相环等分。
"""

from __future__ import annotations

import numpy as np

# Java ColorMapping.color64，单位为度。
HUE64: tuple[float, ...] = (
    0.05, 12.49, 19.87, 25.76, 31.02, 35.91, 40.59, 45.18,
    49.76, 54.51, 59.78, 65.20, 70.02, 74.37, 78.53, 82.51,
    86.37, 90.40, 94.95, 100.33, 106.66, 123.21, 134.51, 140.03,
    144.56, 148.67, 152.52, 156.11, 159.72, 163.58, 168.16, 173.81,
    180.00, 185.34, 189.88, 194.14, 198.90, 204.67, 210.83, 217.16,
    224.87, 242.95, 259.28, 265.12, 269.60, 273.71, 277.75, 281.66,
    285.49, 289.30, 293.30, 297.58, 302.12, 306.64, 311.05, 315.35,
    319.55, 323.74, 327.95, 332.14, 336.42, 341.03, 346.36, 352.67,
)

# createpic_chosen_new.m 里的 16 色编码色，即 HUE64 每隔 4 个取一档。
CODING16: tuple[float, ...] = (
    0.05, 31.02, 49.76, 70.02, 86.37, 106.66, 144.56, 159.72,
    180.00, 198.90, 224.87, 269.60, 285.49, 302.12, 319.55, 336.42,
)

# 帧信息固定 4 色，不随数据色数 N 变化（专利步骤 A1）。
FRAME_HUES: tuple[float, ...] = (0.0, 90.0, 180.0, 270.0)
FRAME_BOUNDS: tuple[float, ...] = (45.0, 135.0, 225.0, 315.0)

POWER_OF_TWO = (2, 4, 8, 16, 32, 64)


def measured_palette(n: int) -> tuple[np.ndarray, np.ndarray]:
    """返回 (编码色相, 色板边界)，长度都是 n。

    编码色是 64 色表的等间隔下采样。色板边界取相邻编码色之间的那一档
    （专利里把差异函数积分一分为二的判定色相；历史代码则直接画在码的侧面）。
    ``bounds[i]`` 是编码色 ``i`` 的上界：色相落在 ``(bounds[i-1], bounds[i]]`` 判为 i。
    """

    if n not in POWER_OF_TWO:
        raise ValueError(f"颜色数量必须是 2 的幂，收到 {n}")
    step = 64 // n
    coding = np.array([HUE64[i * step] for i in range(n)], dtype=float)
    if 64 % (2 * n) == 0:
        half = 64 // (2 * n)
        bounds = np.array([HUE64[(2 * i + 1) * half] for i in range(n)], dtype=float)
    else:
        bounds = np.empty(n, dtype=float)
        for i in range(n):
            span = (coding[(i + 1) % n] - coding[i]) % 360.0
            bounds[i] = (coding[i] + span / 2.0) % 360.0
    return coding, bounds


def hue_to_rgb(hue: float, saturation: float = 1.0, value: float = 1.0) -> np.ndarray:
    """HSV 色相（度）转到 0–255 的 RGB。色相 0 为红。"""

    h = (hue % 360.0) / 60.0
    c = value * saturation
    x = c * (1.0 - abs(h % 2.0 - 1.0))
    m = value - c
    sector = int(h) % 6
    rgb = (
        (c, x, 0.0),
        (x, c, 0.0),
        (0.0, c, x),
        (0.0, x, c),
        (x, 0.0, c),
        (c, 0.0, x),
    )[sector]
    return np.array([round((channel + m) * 255.0) for channel in rgb], dtype=np.uint8)


def rgb_image_to_hsv(image: np.ndarray) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """uint8 RGB 图像转到色相（度）、饱和度、明度，后两者为 0–1。"""

    x = image.astype(np.float32) / 255.0
    r, g, b = x[:, :, 0], x[:, :, 1], x[:, :, 2]
    mx = np.max(x, axis=2)
    mn = np.min(x, axis=2)
    df = mx - mn
    safe = df > 1e-8
    is_r = (mx == r) & safe
    is_g = (mx == g) & ~is_r & safe
    is_b = safe & ~is_r & ~is_g
    hue = np.zeros_like(mx)
    hue[is_r] = np.mod((g[is_r] - b[is_r]) / df[is_r], 6.0)
    hue[is_g] = (b[is_g] - r[is_g]) / df[is_g] + 2.0
    hue[is_b] = (r[is_b] - g[is_b]) / df[is_b] + 4.0
    hue = (hue / 6.0) % 1.0 * 360.0
    saturation = np.zeros_like(mx)
    nz = mx > 1e-8
    saturation[nz] = df[nz] / mx[nz]
    return hue, saturation, mx


def mean_hue(rgb_pixels: np.ndarray, saturation_min: float = 0.35) -> float:
    """对一组 RGB 像素做圆周平均色相。饱和度过低的点不参与。"""

    if rgb_pixels.size == 0:
        return 0.0
    patch = rgb_pixels.reshape(1, -1, 3)
    hue, sat, _ = rgb_image_to_hsv(patch)
    chosen = hue[0][sat[0] >= saturation_min]
    if chosen.size == 0:
        return 0.0
    ang = np.deg2rad(chosen.astype(float))
    return float(np.rad2deg(np.arctan2(np.sin(ang).mean(), np.cos(ang).mean())) % 360.0)
