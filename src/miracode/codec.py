"""分段、掩码、帧信息和色相归类。

掩码是收发双方都知道的确定性序列：专利要求避免某一色过多，
历史 ``mask_generator.m`` 也是预先生成、两端共用，只是当时抽的是 0、1、2。
帧信息固定 4 色，内容是总帧数、帧号和本帧数据长度，并带 RS。
"""

from __future__ import annotations

import math
import struct

import numpy as np

from miracode.errors import DecodeError
from miracode.reedsolo import ReedSolomon

INFO_PAYLOAD_BYTES = 6
INFO_PARITY = 4
# 一帧拆成若干个 32+16 的短码字，保证不超过 RS 的 255 字节上限。
RS_DATA = 32
RS_PARITY = 16
RS_BLOCK = RS_DATA + RS_PARITY


class SymbolCodec:
    """一帧数据的掩码、Reed-Solomon 和 4 色帧信息。"""

    INFO_PAYLOAD_BYTES = INFO_PAYLOAD_BYTES
    INFO_PARITY = INFO_PARITY
    RS_DATA = RS_DATA
    RS_PARITY = RS_PARITY
    RS_BLOCK = RS_BLOCK

    def __init__(self, n_colors: int) -> None:
        self.n_colors = n_colors
        self.bits = self.bits_per_symbol(n_colors)
        self.data_code = ReedSolomon(self.RS_PARITY)
        self.info_code = ReedSolomon(self.INFO_PARITY)

    @staticmethod
    def bits_per_symbol(n_colors: int) -> int:
        bits = int(round(math.log2(n_colors)))
        if 1 << bits != n_colors:
            raise ValueError("颜色数必须是 2 的幂")
        return bits

    def mask(self, symbols: list[int], undo: bool = False) -> list[int]:
        out = []
        for index, symbol in enumerate(symbols):
            delta = (index * 17 + 3) % self.n_colors
            if undo:
                out.append((symbol - delta) % self.n_colors)
            else:
                out.append((symbol + delta) % self.n_colors)
        return out

    def payload_capacity(self, symbol_count: int) -> int:
        raw = symbol_count * self.bits // 8
        if raw % self.RS_BLOCK != 0:
            raise ValueError("版面字节数无法排满 RS 短码字")
        return (raw // self.RS_BLOCK) * self.RS_DATA

    def encode_data(self, chunk: bytes, symbol_count: int) -> list[int]:
        capacity = self.payload_capacity(symbol_count)
        if len(chunk) > capacity:
            raise ValueError("单帧数据超过容量")
        body = chunk + bytes(capacity - len(chunk))
        coded = b"".join(
            self.data_code.encode(body[offset : offset + self.RS_DATA]) for offset in range(0, len(body), self.RS_DATA)
        )
        return self.mask(self._bytes_to_symbols(coded, symbol_count))

    def decode_data(self, symbols: list[int], length: int) -> bytes:
        raw = len(symbols) * self.bits // 8
        coded = self._symbols_to_bytes(self.mask(symbols, undo=True), raw)
        parts = [
            self.data_code.decode(coded[offset : offset + self.RS_BLOCK])
            for offset in range(0, len(coded), self.RS_BLOCK)
        ]
        body = b"".join(parts)
        if length > len(body):
            raise DecodeError("帧信息里的长度超出本帧容量")
        return body[:length]

    def encode_frame_info(self, total: int, index: int, length: int) -> list[int]:
        if not 0 <= index < total <= 65535 or not 0 <= length <= 65535:
            raise ValueError("帧号或长度超出帧信息字段")
        coded = self.info_code.encode(struct.pack(">HHH", total, index, length))
        symbols = []
        for byte in coded:
            for shift in (6, 4, 2, 0):
                symbols.append((byte >> shift) & 0x3)
        return symbols

    def decode_frame_info(self, symbols: list[int]) -> tuple[int, int, int]:
        needed = (self.INFO_PAYLOAD_BYTES + self.INFO_PARITY) * 4
        if len(symbols) < needed:
            raise DecodeError("帧信息色块不够")
        out = bytearray()
        for offset in range(0, needed, 4):
            byte = 0
            for symbol in symbols[offset : offset + 4]:
                byte = (byte << 2) | int(symbol)
            out.append(byte)
        total, index, length = struct.unpack(">HHH", self.info_code.decode(bytes(out)))
        return int(total), int(index), int(length)

    def _bytes_to_symbols(self, data: bytes, count: int) -> list[int]:
        symbols: list[int] = []
        buffer = 0
        filled = 0
        for byte in data:
            buffer = (buffer << 8) | byte
            filled += 8
            while filled >= self.bits:
                filled -= self.bits
                symbols.append((buffer >> filled) & ((1 << self.bits) - 1))
        if len(symbols) < count:
            symbols.extend([0] * (count - len(symbols)))
        if len(symbols) != count:
            raise ValueError("符号个数超出版面")
        return symbols

    def _symbols_to_bytes(self, symbols: list[int], nbytes: int) -> bytes:
        buffer = 0
        filled = 0
        out = bytearray()
        for symbol in symbols:
            buffer = (buffer << self.bits) | int(symbol)
            filled += self.bits
            while filled >= 8 and len(out) < nbytes:
                filled -= 8
                out.append((buffer >> filled) & 0xFF)
        if len(out) < nbytes:
            raise DecodeError("色块不足以还原字节")
        return bytes(out)


class HueClassifier:
    """按色板上界把一个色相判成色号。"""

    @staticmethod
    def in_sector(hue: float, start: float, end: float) -> bool:
        """半开区间 (start, end]，跨过 0° 时仍然成立。"""

        hue %= 360.0
        start %= 360.0
        end %= 360.0
        if start < end:
            return start < hue <= end
        if start > end:
            return hue > start or hue <= end
        return False

    @classmethod
    def classify(cls, hue: float, bounds: np.ndarray) -> int:
        """bounds[i] 是颜色 i 的上界。"""

        count = len(bounds)
        for index in range(count):
            start = float(bounds[(index - 1) % count])
            end = float(bounds[index])
            if cls.in_sector(hue, start, end):
                return index
        hue %= 360.0
        distances = [min((hue - float(bound)) % 360.0, (float(bound) - hue) % 360.0) for bound in bounds]
        return int(np.argmin(distances))
