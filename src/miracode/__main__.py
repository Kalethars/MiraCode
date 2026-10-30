"""命令行：做一次往返。"""

from __future__ import annotations

import argparse
import sys

from miracode.pipeline import MiraCode


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="MiraCode 彩色二维码流")
    sub = parser.add_subparsers(dest="command", required=True)
    roundtrip = sub.add_parser("roundtrip", help="编码后再解码一段文本")
    roundtrip.add_argument("--text", default="MiraCode 四维码")
    roundtrip.add_argument("--colors", type=int, default=16)
    args = parser.parse_args(argv)
    if args.command == "roundtrip":
        link = MiraCode(args.colors)
        payload = args.text.encode("utf-8")
        restored = link.decode(link.encode(payload))
        if restored != payload:
            print("往返失败", file=sys.stderr)
            return 1
        print(restored.decode("utf-8"))
        return 0
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
