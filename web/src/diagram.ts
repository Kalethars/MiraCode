export const FLOW = `flowchart TD
  A[文字切成帧] --> B[附校验和掩膜]
  B --> C[写入帧信息和彩色色块]
  C --> D[逐帧显示到屏幕]
  D --> E[相机拍摄]
  E --> F[黑极化找定位图案]
  F --> G{两帧叠在一起吗}
  G -->|是| H[丢弃这张照片]
  G -->|否| I[拉正并按色板认色]
  I --> J[纠错去掩膜]
  J --> K[按帧号拼回文字]
  classDef send fill:#fdf4e3,stroke:#c9a24d,color:#3a2f1f
  classDef recv fill:#eef3fb,stroke:#8aa5c8,color:#24303f
  classDef warn fill:#fdecec,stroke:#c96a6a,color:#402424
  class A,B,C,D send
  class E,F,G,I,J,K recv
  class H warn
`;
