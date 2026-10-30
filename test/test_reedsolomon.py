"""Reed-Solomon、掩码和帧信息。"""

from __future__ import annotations

import unittest

import support
from miracode.codec import SymbolCodec
from miracode.reedsolo import ReedSolomon

support


class TestReedSolomon(unittest.TestCase):
    def test_clean_codeword_roundtrip(self) -> None:
        data = bytes(range(20))
        code = ReedSolomon(8)
        self.assertEqual(code.decode(code.encode(data)), data)

    def test_corrects_two_byte_errors(self) -> None:
        data = bytes([((i * 17) + 3) % 256 for i in range(32)])
        code = ReedSolomon(8)
        coded = bytearray(code.encode(data))
        coded[1] ^= 0x5A
        coded[20] ^= 0x11
        self.assertEqual(code.decode(bytes(coded)), data)

    def test_frame_info_survives_a_symbol_error(self) -> None:
        codec = SymbolCodec(16)
        symbols = codec.encode_frame_info(total=3, index=1, length=40)
        symbols[2] ^= 0x1
        self.assertEqual(codec.decode_frame_info(symbols), (3, 1, 40))


class TestMaskAndPayload(unittest.TestCase):
    def test_mask_is_reversible(self) -> None:
        codec = SymbolCodec(16)
        symbols = [i % 16 for i in range(50)]
        self.assertEqual(codec.mask(codec.mask(symbols), undo=True), symbols)

    def test_data_symbols_roundtrip_and_correct_a_block(self) -> None:
        codec = SymbolCodec(16)
        capacity = codec.payload_capacity(32 * 24)
        payload = bytes([i % 251 for i in range(capacity)])
        symbols = codec.encode_data(payload, 32 * 24)
        broken = symbols[:]
        broken[10] = (broken[10] + 1) % 16
        broken[200] = (broken[200] + 3) % 16
        self.assertEqual(codec.decode_data(broken, len(payload)), payload)
