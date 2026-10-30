"""MiraCode 解码错误。"""


class MiraCodeError(Exception):
    """编解码失败。"""


class MixedFrame(MiraCodeError):
    """定位图案的红绿通道同时偏高，判定为相邻帧混叠。"""


class DecodeError(MiraCodeError):
    """定位、校验或帧信息无法恢复。"""
