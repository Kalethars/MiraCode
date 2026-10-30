"""定位训练仓库里的原始实拍，不把路径写死。"""

from __future__ import annotations

import os
from pathlib import Path


class SourcePhotos:
    """MiraCode-training 里的原始照片。"""

    def __init__(self, root: Path) -> None:
        self.root = root
        self.hue360 = root / "hue360"
        self.stability = root / "stability"

    @classmethod
    def discover(cls) -> SourcePhotos:
        env = os.environ.get("MIRACODE_TRAINING")
        if env:
            root = Path(env)
        else:
            root = Path(__file__).resolve().parents[2].parent / "MiraCode-training"
        photos = cls(root)
        if not photos.hue360.is_dir() or not photos.stability.is_dir():
            raise FileNotFoundError("找不到原始照片目录 hue360 和 stability")
        return photos

    def hue_capture(self, index: int) -> Path:
        matches = list(self.hue360.glob(f"1 ({index}).jpg")) + list(self.hue360.glob(f"1 ({index}).JPG"))
        if not matches:
            raise FileNotFoundError(f"缺少色相连拍 1 ({index})")
        return matches[0]

    def stability_burst(self, prefix: str) -> list[Path]:
        files = [
            path
            for path in self.stability.iterdir()
            if path.is_file() and path.name.startswith(prefix + " (") and path.suffix.lower() in {".jpg", ".jpeg"}
        ]
        return sorted(files, key=lambda path: path.name)
