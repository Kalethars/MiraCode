export const FLOW = `flowchart LR
  subgraph 发送
    direction TB
    A[文字切成帧] --> B[每帧附校验和掩膜]
    B --> C[写入帧信息和彩色色块]
    C --> D[逐帧显示到屏幕]
  end
  subgraph 接收
    direction TB
    E[相机拍摄] --> F[黑极化找定位图案]
    F --> G{两帧叠在一起?}
    G -- 是 --> H[丢弃这张照片]
    G -- 否 --> I[拉正并按色板认色]
    I --> J[纠错去掩膜]
    J --> K[按帧号拼回文字]
  end
  D --> E
`;
