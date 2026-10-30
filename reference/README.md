# 历史代码

这里只留 MiraCode 真正用过的脚本，作为 Python 实现的对照，不是完整实验目录。

| 路径 | 作用 |
| --- | --- |
| `color/ColorMapping.java` | 64 色实测色相，以及编码色 / 色板色的下采样 |
| `render/createpic_chosen_new.m` | 16 色码的定位图案、参考色和数据区画法 |
| `render/generate_standard.py` | 参考色在边框上的 8/11 步进 |
| `render/createpic_chosen_new_2016.m` | 2016 年的画码脚本 |
| `decode/analyse_16color.m` | 按参考色区间认色块 |
| `decode/analyse_final.m` | 定稿识别 |
| `decode/generatetable.m` | 从参考色生成色号表 |
| `decode/compare.m` | 用一组实测边界 `ref2` 统计识别率 |
| `decode/capacity.m` | 识别率换成容量 |
| `encode/Encode.m`、`Encode_16.m` | 把明文铺进色块 |
| `encode/mask_generator.m` | 预先生成、两端共用的掩码 |
| `stream/Cipher.m`、`Decipher.m` | 2016 年在码流外包的一层替换 |

实验照片、幻灯片和论文 PDF 没有放进来。
