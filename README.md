# MiraCode

基于色相的容量可变彩色二维码流。屏幕逐帧显示彩色码，摄像头拍照后解码。颜色是第三维，帧序列是第四维。

专利是 [CN106056021A](https://patents.google.com/patent/CN106056021A/zh)（上海交通大学，朱思宇、张晔、赵性雅、王新兵、甘小莺）。论文是 *MiraCode: Multi-color Barcode Streaming*。历史 MATLAB / Java 在 `reference/`。

本仓库以 [Apache License 2.0](LICENSE) 授权。这份协议同时包含著作权许可，以及贡献者就其贡献作出的专利许可。

三边不一致的地方，按下面的方式取舍：

- **流程**跟专利：颜色数必须是 2 的幂；先按识别率选容量最大的色数；每帧加 Reed-Solomon、两端已知的掩码和帧信息；帧信息只用 4 色。接收端黑极化，找定位图案，混叠就丢，再用色板区间认色，纠错、去掩码、按帧号拼文件。
- **选色**跟专利的差异函数积分，起点跟论文放在最稳的青色 H=180。分子用论文的相邻色相差，分母用专利的标准差。没有实测曲线时，直接用历史代码里的 64 色表。
- **版面**跟专利的结构，尺寸跟历史代码：16 像素色块，定位图案宽度比 1:1:2:1:1。四个角里较小的那个用来定方向。定位环在相邻帧之间红绿交替，红绿同时偏高就当混叠丢掉。黑白定位参考线夹着数据区，两侧是色板。

## 环境

需要 Python 3.10 和 NumPy。论文用的色相汇总已经收成默认参数 `src/miracode/defaults/parameters.json`，程序不读取原来的制表符文本。

最源头的实拍照片在单独的 Git LFS 仓库，不在本仓库里：

https://gitlab.com/Kalethars/MiraCode-training

```text
python -m unittest discover -s test -v
```

试玩页在浏览器里完成生成和解码，并附有一张全过程示意图：

https://kalethars.github.io/MiraCode/

页面源码在 `web/`。GitHub Actions 在推送到 `main` 后把它发布到 GitHub Pages。

## 目录

| 路径 | 内容 |
| --- | --- |
| `src/miracode/` | Python 全流程 |
| `reference/` | 历史脚本 |
| `test/` | 单元测试、往返，以及训练后写视频再解码 |
| `web/` | 浏览器试玩页：生成视频、解码视频，并用一张图说明全过程 |

`train` 用默认参数里的差分和标准差估计各档颜色数的识别率，并选出容量最大的一档。`video` 把帧写成无压缩 AVI，再读回来解码。

编码示例：

```text
PYTHONPATH=src python -m miracode roundtrip --text MiraCode
```

在仓库根目录跑测试时，测试会自己把 `src` 加进模块路径。命令行需要 `PYTHONPATH=src`。
