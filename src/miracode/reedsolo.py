"""字节上的 Reed-Solomon，GF(2^8)，本原多项式 0x11d。

专利要求每帧再按固定长度分段加校验。单个码字不超过 255 字节，
所以一帧里会排多个短码字，而不是一整帧一个码字。
"""

from __future__ import annotations

from miracode.errors import DecodeError


class _GF:
    def __init__(self) -> None:
        self.exp = [0] * 512
        self.log = [0] * 256
        value = 1
        for power in range(255):
            self.exp[power] = value
            self.log[value] = power
            value <<= 1
            if value & 0x100:
                value ^= 0x11D
        for power in range(255, 512):
            self.exp[power] = self.exp[power - 255]

    def mul(self, left: int, right: int) -> int:
        if left == 0 or right == 0:
            return 0
        return self.exp[self.log[left] + self.log[right]]

    def inv(self, value: int) -> int:
        if value == 0:
            raise ZeroDivisionError
        return self.exp[255 - self.log[value]]


GF = _GF()


def _generator(nsym: int) -> list[int]:
    # 最高次在前：下标 0 是 x^{nsym} 的系数。
    poly = [1]
    for power in range(nsym):
        product = [0] * (len(poly) + 1)
        for index, coef in enumerate(poly):
            product[index] ^= coef
            product[index + 1] ^= GF.mul(coef, GF.exp[power])
        poly = product
    return poly


def encode(data: bytes, nsym: int) -> bytes:
    """返回 data 接 nsym 个校验字节。"""

    if nsym <= 0:
        raise ValueError("校验字节数必须为正")
    if len(data) + nsym > 255:
        raise ValueError("RS 码字最长 255 字节")
    generator = _generator(nsym)
    message = list(data) + [0] * nsym
    for index in range(len(data)):
        coef = message[index]
        if coef == 0:
            continue
        for offset in range(1, len(generator)):
            message[index + offset] ^= GF.mul(generator[offset], coef)
    return bytes(list(data) + message[-nsym:])


def _syndromes(codeword: list[int], nsym: int) -> list[int]:
    syndromes = []
    for power in range(nsym):
        acc = 0
        root = GF.exp[power]
        for coef in codeword:
            acc = GF.mul(acc, root) ^ coef
        syndromes.append(acc)
    return syndromes


def _berlekamp_massey(syndromes: list[int]) -> list[int]:
    # 常数项在前。
    locator = [1]
    previous = [1]
    length = 0
    shift = 1
    last = 1
    for n, syndrome in enumerate(syndromes):
        delta = syndrome
        for i in range(1, length + 1):
            delta ^= GF.mul(locator[i], syndromes[n - i])
        if delta == 0:
            shift += 1
            continue
        scale = GF.mul(delta, GF.inv(last))
        term = [0] * shift + previous
        if len(locator) < len(term):
            locator = locator + [0] * (len(term) - len(locator))
        updated = locator[:]
        for i, coef in enumerate(term):
            updated[i] ^= GF.mul(scale, coef)
        if 2 * length <= n:
            previous = locator
            locator = updated
            length = n + 1 - length
            last = delta
            shift = 1
        else:
            locator = updated
            shift += 1
    while len(locator) > 1 and locator[-1] == 0:
        locator.pop()
    return locator


def _eval_low(poly: list[int], x: int) -> int:
    acc = 0
    power = 1
    for coef in poly:
        acc ^= GF.mul(coef, power)
        power = GF.mul(power, x)
    return acc


def _error_positions(locator: list[int], length: int) -> list[int]:
    """校验子满足 S_k = Σ Y α^{k(n-1-pos)}。定位多项式的根是 α^{-(n-1-pos)}。"""

    positions = []
    for pos in range(length):
        exponent = (255 - (length - 1 - pos)) % 255
        if _eval_low(locator, GF.exp[exponent]) == 0:
            positions.append(pos)
    return positions


def _solve(matrix: list[list[int]], values: list[int]) -> list[int]:
    size = len(values)
    rows = [matrix[i][:] + [values[i]] for i in range(size)]
    for col in range(size):
        pivot = next((row for row in range(col, size) if rows[row][col] != 0), None)
        if pivot is None:
            raise DecodeError("RS 错误幅度方程组奇异")
        rows[col], rows[pivot] = rows[pivot], rows[col]
        inverse = GF.inv(rows[col][col])
        for index in range(col, size + 1):
            rows[col][index] = GF.mul(rows[col][index], inverse)
        for row in range(size):
            if row == col or rows[row][col] == 0:
                continue
            factor = rows[row][col]
            for index in range(col, size + 1):
                rows[row][index] ^= GF.mul(factor, rows[col][index])
    return [rows[i][size] for i in range(size)]


def _magnitudes(syndromes: list[int], positions: list[int], length: int) -> list[int]:
    xs = [GF.exp[(length - 1 - pos) % 255] for pos in positions]
    matrix = []
    for power in range(len(positions)):
        row = []
        for x in xs:
            value = 1
            for _ in range(power):
                value = GF.mul(value, x)
            row.append(value)
        matrix.append(row)
    return _solve(matrix, syndromes[: len(positions)])


class ReedSolomon:
    """一帧里的一个短码字。校验字节数在构造时定死。"""

    def __init__(self, parity_bytes: int) -> None:
        if parity_bytes <= 0:
            raise ValueError("校验字节数必须为正")
        self.parity_bytes = parity_bytes

    def encode(self, data: bytes) -> bytes:
        return encode(data, self.parity_bytes)

    def decode(self, codeword: bytes) -> bytes:
        return decode(codeword, self.parity_bytes)


def decode(codeword: bytes, nsym: int) -> bytes:
    """纠正最多 nsym//2 个字节错误，返回数据部分。"""

    if nsym <= 0 or nsym >= len(codeword):
        raise DecodeError("RS 码字长度不合法")
    message = list(codeword)
    syndromes = _syndromes(message, nsym)
    if all(value == 0 for value in syndromes):
        return bytes(message[:-nsym])
    locator = _berlekamp_massey(syndromes)
    degree = len(locator) - 1
    if degree <= 0 or degree > nsym // 2:
        raise DecodeError("RS 错误个数超出校验能力")
    positions = _error_positions(locator, len(message))
    if len(positions) != degree:
        raise DecodeError("RS 错误位置找不到")
    for pos, magnitude in zip(positions, _magnitudes(syndromes, positions, len(message))):
        message[pos] ^= magnitude
    if any(value != 0 for value in _syndromes(message, nsym)):
        raise DecodeError("RS 纠错后校验子不为零")
    return bytes(message[:-nsym])
