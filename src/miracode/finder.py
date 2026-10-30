"""黑极化、定位图案和单应性。

黑极化按专利：RGB 三通道都低于阈值才算黑。
定位图案的宽度比用论文和历史作图里的 1:1:2:1:1。
四个角里较小的那个是专利里的特殊定位图案，用来确定方向。
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from miracode.errors import DecodeError, MixedFrame
from miracode.layout import Geometry


@dataclass
class FinderHit:
    y: float
    x: float
    width: float
    votes: int


def polarize(image: np.ndarray, threshold: int = 40) -> np.ndarray:
    """RGB 三通道都低于阈值的像素视为黑。"""

    return np.all(image < threshold, axis=2)


def _runs(mask_line: np.ndarray) -> list[tuple[bool, int, int]]:
    if mask_line.size == 0:
        return []
    changes = np.flatnonzero(mask_line[1:] != mask_line[:-1]) + 1
    bounds = np.concatenate(([0], changes, [mask_line.size]))
    return [(bool(mask_line[start]), int(start), int(bounds[i + 1] - start)) for i, start in enumerate(bounds[:-1])]


def _ratio_ok(lengths: list[int], tolerance: float = 0.45) -> tuple[bool, float]:
    total = float(sum(lengths))
    unit = total / 6.0
    if unit < 4:
        return False, unit
    expected = (unit, unit, 2 * unit, unit, unit)
    ok = all(abs(lengths[i] - expected[i]) <= tolerance * unit for i in range(5))
    return ok, total


def _vertical_ok(mask: np.ndarray, y: float, x: int, tolerance: float = 0.5) -> bool:
    height, width = mask.shape
    if not 0 <= x < width:
        return False
    runs = _runs(mask[:, x])
    for index in range(len(runs) - 4):
        if [runs[index + k][0] for k in range(5)] != [True, False, True, False, True]:
            continue
        lengths = [runs[index + k][2] for k in range(5)]
        ok, _total = _ratio_ok(lengths, tolerance)
        if not ok:
            continue
        center = runs[index + 2][1] + lengths[2] / 2.0
        if abs(center - y) <= lengths[2]:
            return True
    return False


def _cluster(points: list[tuple[float, float, float]], radius: float = 28.0) -> list[FinderHit]:
    groups: list[dict] = []
    for y, x, width in points:
        for group in groups:
            if (y - group["y"]) ** 2 + (x - group["x"]) ** 2 <= radius ** 2:
                group["ys"].append(y)
                group["xs"].append(x)
                group["ws"].append(width)
                group["y"] = float(np.mean(group["ys"]))
                group["x"] = float(np.mean(group["xs"]))
                break
        else:
            groups.append({"y": y, "x": x, "ys": [y], "xs": [x], "ws": [width]})
    hits = []
    for group in groups:
        if len(group["ys"]) < 4:
            continue
        hits.append(FinderHit(group["y"], group["x"], float(np.median(group["ws"])), len(group["ys"])))
    hits.sort(key=lambda hit: hit.votes, reverse=True)
    return hits


def find_finders(image: np.ndarray) -> list[FinderHit]:
    """找出定位图案中心。返回的列表至少应有 4 个，调用方再取票数最高的四个。"""

    mask = polarize(image)
    points: list[tuple[float, float, float]] = []
    for y in range(mask.shape[0]):
        runs = _runs(mask[y])
        for index in range(len(runs) - 4):
            if [runs[index + k][0] for k in range(5)] != [True, False, True, False, True]:
                continue
            lengths = [runs[index + k][2] for k in range(5)]
            ok, total = _ratio_ok(lengths)
            if not ok:
                continue
            center_x = runs[index + 2][1] + lengths[2] / 2.0
            if _vertical_ok(mask, y, int(round(center_x))):
                points.append((float(y), center_x, total))
    return _cluster(points)


def order_corners(hits: list[FinderHit]) -> list[FinderHit]:
    """按特殊（更小）定位图案定方向，返回 TL, TR, BR, BL。

    图像坐标 y 向下，绕质心方位角增大的方向是顺时针。
    未旋转时从左上角顺时针依次是右上、右下、左下。旋转不改变这个相对顺序。
    """

    if len(hits) < 4:
        raise DecodeError(f"只找到 {len(hits)} 个定位图案")
    chosen = sorted(hits, key=lambda hit: hit.votes, reverse=True)[:4]
    special = min(chosen, key=lambda hit: hit.width)
    cy = float(np.mean([hit.y for hit in chosen]))
    cx = float(np.mean([hit.x for hit in chosen]))
    clockwise = sorted(chosen, key=lambda hit: np.arctan2(hit.y - cy, hit.x - cx))
    start = clockwise.index(special)
    ordered = [clockwise[(start + offset) % 4] for offset in range(4)]
    # 顺时针第一个应当是特殊角。若特殊角的宽度并不是明显更小，拒绝这帧。
    widths = sorted(hit.width for hit in ordered)
    if widths[0] > widths[1] * 0.9:
        raise DecodeError("无法区分特殊定位图案")
    return ordered


def homography(design_xy: np.ndarray, image_xy: np.ndarray) -> np.ndarray:
    """四点单应，把版面坐标映射到照片坐标。"""

    matrix = []
    target = []
    for (x, y), (u, v) in zip(design_xy, image_xy):
        matrix.append([x, y, 1, 0, 0, 0, -u * x, -u * y])
        matrix.append([0, 0, 0, x, y, 1, -v * x, -v * y])
        target.extend([u, v])
    coeffs = np.linalg.solve(np.asarray(matrix, dtype=float), np.asarray(target, dtype=float))
    return np.array(
        [[coeffs[0], coeffs[1], coeffs[2]], [coeffs[3], coeffs[4], coeffs[5]], [coeffs[6], coeffs[7], 1.0]],
        dtype=float,
    )


def map_points(transform: np.ndarray, points_xy: np.ndarray) -> np.ndarray:
    pts = np.atleast_2d(np.asarray(points_xy, dtype=float))
    hom = np.concatenate([pts, np.ones((len(pts), 1))], axis=1)
    mapped = hom @ transform.T
    return mapped[:, :2] / mapped[:, 2:3]


def sample_patch(image: np.ndarray, x: float, y: float, radius: int = 2) -> np.ndarray:
    height, width = image.shape[:2]
    xi = int(round(x))
    yi = int(round(y))
    x0, x1 = max(0, xi - radius), min(width, xi + radius + 1)
    y0, y1 = max(0, yi - radius), min(height, yi + radius + 1)
    if x0 >= x1 or y0 >= y1:
        raise DecodeError("采样点落在图像外")
    return image[y0:y1, x0:x1].reshape(-1, 3)


def ring_is_mixed(image: np.ndarray, hit: FinderHit) -> bool:
    """定位环上红、绿都高，则这张照片是两帧叠在一起。"""

    radius = hit.width / 4.0
    samples = []
    for step in range(8):
        angle = step * np.pi / 4.0
        x = hit.x + radius * np.cos(angle)
        y = hit.y + radius * np.sin(angle)
        samples.append(sample_patch(image, x, y, radius=1).mean(axis=0))
    rgb = np.mean(samples, axis=0)
    red, green, blue = (float(rgb[0]), float(rgb[1]), float(rgb[2]))
    return red > 90 and green > 90 and blue < 100 and abs(red - green) < 50


class FrameLocator:
    """在一帧照片里找出码的位置，并采样版面上的点。"""

    def __init__(self, geometry: Geometry) -> None:
        self.geometry = geometry

    def locate(self, image: np.ndarray) -> tuple[np.ndarray, list[FinderHit]]:
        """返回单应矩阵，以及按 TL, TR, BR, BL 排好的定位图案。混叠帧直接拒绝。"""

        hits = find_finders(image)
        corners = order_corners(hits)
        if any(ring_is_mixed(image, hit) for hit in corners):
            raise MixedFrame("定位图案红绿混叠，丢弃该帧")
        image_xy = np.array([[hit.x, hit.y] for hit in corners], dtype=float)
        return homography(self.geometry.design_corners(), image_xy), corners

    def map_design(self, transform: np.ndarray, points_xy: np.ndarray) -> np.ndarray:
        return map_points(transform, points_xy)

    def sample(self, image: np.ndarray, x: float, y: float, radius: int = 2) -> np.ndarray:
        return sample_patch(image, x, y, radius)
