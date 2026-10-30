"""把二维码帧写成无压缩 AVI，再按原样读回来。

不依赖 OpenCV。像素按 BGR、自下而上存放，读写互逆，色相不会被压缩破坏。
"""

from __future__ import annotations

import struct
from pathlib import Path

import numpy as np


def _chunk(tag: bytes, payload: bytes) -> bytes:
    pad = b"\x00" if len(payload) % 2 else b""
    return tag + struct.pack("<I", len(payload)) + payload + pad


def _list(kind: bytes, payload: bytes) -> bytes:
    return _chunk(b"LIST", kind + payload)


def _frame_blob(frame: np.ndarray) -> bytes:
    if frame.ndim != 3 or frame.shape[2] != 3 or frame.dtype != np.uint8:
        raise ValueError("视频帧必须是 uint8 RGB")
    height, width, _ = frame.shape
    stride = (width * 3 + 3) & ~3
    bgr = np.ascontiguousarray(frame[:, :, ::-1])
    padded = np.zeros((height, stride), dtype=np.uint8)
    padded[:, : width * 3] = bgr.reshape(height, width * 3)
    return np.ascontiguousarray(np.flipud(padded)).tobytes()


class AviVideo:
    """无压缩 AVI。像素按 BGR、自下而上存放。"""

    def __init__(self, frames: list[np.ndarray] | None = None, fps: int = 10) -> None:
        self.frames = list(frames or [])
        self.fps = fps

    def write(self, path: str | Path) -> None:
        _write_avi(path, self.frames, self.fps)

    @classmethod
    def read(cls, path: str | Path) -> AviVideo:
        return cls(_read_avi(path))


def _write_avi(path: str | Path, frames: list[np.ndarray], fps: int = 10) -> None:
    if not frames:
        raise ValueError("没有帧可以写入")
    if fps <= 0:
        raise ValueError("帧率必须为正")
    blobs = [_frame_blob(frame) for frame in frames]
    height, width = frames[0].shape[:2]
    if any(frame.shape[:2] != (height, width) for frame in frames):
        raise ValueError("各帧尺寸不一致")
    frame_size = len(blobs[0])
    avih = struct.pack(
        "<14I",
        int(1_000_000 / fps),
        frame_size * fps,
        0,
        0,
        len(frames),
        0,
        1,
        frame_size,
        width,
        height,
        0,
        0,
        0,
        0,
    )
    strh = struct.pack(
        "<4s4sIHHIIIIIIIIhhhh",
        b"vids",
        b"DIB ",
        0,
        0,
        0,
        0,
        1,
        fps,
        0,
        len(frames),
        frame_size,
        0xFFFFFFFF,
        0,
        0,
        0,
        width,
        height,
    )
    strf = struct.pack("<IiiHHIIiiII", 40, width, height, 1, 24, 0, frame_size, 0, 0, 0, 0)
    hdrl = _list(
        b"hdrl",
        _chunk(b"avih", avih) + _list(b"strl", _chunk(b"strh", strh) + _chunk(b"strf", strf)),
    )
    movi_payload = b"movi" + b"".join(_chunk(b"00db", blob) for blob in blobs)
    movi = _chunk(b"LIST", movi_payload)
    body = hdrl + movi
    avi = b"RIFF" + struct.pack("<I", 4 + len(body)) + b"AVI " + body
    Path(path).write_bytes(avi)


def _read_avi(path: str | Path) -> list[np.ndarray]:
    data = Path(path).read_bytes()
    if data[:4] != b"RIFF" or data[8:12] != b"AVI ":
        raise ValueError("不是 AVI 文件")
    strf_at = data.find(b"strf")
    if strf_at < 0:
        raise ValueError("AVI 缺少位图头")
    header = data[strf_at + 8 : strf_at + 8 + 40]
    _size, width, height, _planes, bit_count, _compression, _image_size, *_rest = struct.unpack("<IiiHHIIiiII", header)
    if bit_count != 24:
        raise ValueError("只读取 24 位无压缩 AVI")
    stride = (width * 3 + 3) & ~3
    frames: list[np.ndarray] = []
    cursor = 12
    while True:
        at = data.find(b"00db", cursor)
        if at < 0:
            break
        size = struct.unpack_from("<I", data, at + 4)[0]
        raw = data[at + 8 : at + 8 + size]
        if len(raw) < abs(height) * stride:
            break
        plane = np.frombuffer(raw[: abs(height) * stride], dtype=np.uint8).reshape(abs(height), stride)
        plane = np.flipud(plane)[:, : width * 3].reshape(abs(height), width, 3)
        frames.append(np.ascontiguousarray(plane[:, :, ::-1]))
        cursor = at + 8 + size + (size % 2)
    if not frames:
        raise ValueError("AVI 里没有视频帧")
    return frames
