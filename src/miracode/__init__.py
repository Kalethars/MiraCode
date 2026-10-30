"""MiraCode：基于色相的容量可变彩色二维码流。

实现依据是专利 CN106056021A、MiraCode 论文，以及 ``reference/`` 里的历史脚本。
"""

from miracode.codec import HueClassifier, SymbolCodec
from miracode.color_selection import ColorSelector
from miracode.errors import DecodeError, MiraCodeError, MixedFrame
from miracode.layout import FramePainter, Geometry
from miracode.palette import CODING16, HUE64
from miracode.pipeline import DecodedFrame, MiraCode
from miracode.train import ColorModel, load_defaults
from miracode.video import AviVideo

__all__ = [
    "CODING16",
    "HUE64",
    "AviVideo",
    "ColorModel",
    "ColorSelector",
    "DecodeError",
    "DecodedFrame",
    "FramePainter",
    "Geometry",
    "HueClassifier",
    "MiraCode",
    "MiraCodeError",
    "MixedFrame",
    "SymbolCodec",
    "load_defaults",
]
