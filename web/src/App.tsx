import { useEffect, useRef, useState } from "react";
import mermaid from "mermaid";
import { FLOW } from "./diagram";
import { MiraCode } from "./miracode/pipeline";
import { RgbImage } from "./miracode/layout";
import { readAvi, writeAvi } from "./miracode/video";

mermaid.initialize({
  startOnLoad: false,
  securityLevel: "strict",
  theme: "base",
  themeVariables: {
    fontFamily: '"Segoe UI", "PingFang SC", "Noto Sans SC", sans-serif',
    fontSize: "14px",
    primaryColor: "#fffdf8",
    primaryTextColor: "#241f19",
    primaryBorderColor: "#c9b99d",
    lineColor: "#8a7a63",
    textColor: "#241f19",
    clusterBkg: "#fbf7ef",
    clusterBorder: "#d8cbb8",
    edgeLabelBackground: "#fffdf8",
  },
});

function paint(canvas: HTMLCanvasElement, image: RgbImage): void {
  const ctx = canvas.getContext("2d");
  if (!ctx) return;
  canvas.width = image.width;
  canvas.height = image.height;
  const pixels = ctx.createImageData(image.width, image.height);
  for (let i = 0, j = 0; i < image.data.length; i += 3, j += 4) {
    pixels.data[j] = image.data[i];
    pixels.data[j + 1] = image.data[i + 1];
    pixels.data[j + 2] = image.data[i + 2];
    pixels.data[j + 3] = 255;
  }
  ctx.putImageData(pixels, 0, 0);
}

export function App() {
  const diagramRef = useRef<HTMLDivElement>(null);
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const [text, setText] = useState("MiraCode 把颜色当作第三维，把连续帧当作第四维。");
  const [colors, setColors] = useState(16);
  const [status, setStatus] = useState("在浏览器里完成编码和解码，不需要服务器。");
  const [download, setDownload] = useState<string | null>(null);
  const [decoded, setDecoded] = useState("");
  const [busy, setBusy] = useState(false);
  const [frameLabel, setFrameLabel] = useState("");

  useEffect(() => {
    let cancelled = false;
    mermaid.render("miracode-flow", FLOW).then(({ svg }) => {
      if (!cancelled && diagramRef.current) diagramRef.current.innerHTML = svg;
    });
    return () => {
      cancelled = true;
    };
  }, []);

  useEffect(() => () => {
    if (download) URL.revokeObjectURL(download);
  }, [download]);

  async function generate(): Promise<void> {
    setBusy(true);
    setStatus("正在把文字编成彩色帧…");
    await new Promise((resolve) => setTimeout(resolve, 30));
    try {
      const payload = new TextEncoder().encode(text);
      const frames = new MiraCode(colors).encode(payload);
      const avi = writeAvi(frames, 8);
      const url = URL.createObjectURL(new Blob([avi], { type: "video/avi" }));
      setDownload((previous) => {
        if (previous) URL.revokeObjectURL(previous);
        return url;
      });
      if (canvasRef.current) paint(canvasRef.current, frames[0]);
      setFrameLabel(`共 ${frames.length} 帧，预览第 1 帧。每帧 ${frames[0].width}×${frames[0].height} 像素。`);
      setStatus("已生成无压缩 AVI。浏览器通常不能直接播放这种视频，请下载后用上方的解码来还原文字。");
    } catch (error) {
      setStatus(error instanceof Error ? error.message : "生成失败");
    } finally {
      setBusy(false);
    }
  }

  async function decodeFile(file: File): Promise<void> {
    setBusy(true);
    setStatus("正在读取视频并定位每一帧…");
    await new Promise((resolve) => setTimeout(resolve, 30));
    try {
      const bytes = new Uint8Array(await file.arrayBuffer());
      const frames = readAvi(bytes);
      if (canvasRef.current) paint(canvasRef.current, frames[0]);
      setFrameLabel(`读到 ${frames.length} 帧。`);
      const payload = new MiraCode(colors).decode(frames);
      setDecoded(new TextDecoder().decode(payload));
      setStatus("解码完成。");
    } catch (error) {
      setDecoded("");
      setStatus(error instanceof Error ? error.message : "解码失败");
    } finally {
      setBusy(false);
    }
  }

  return (
    <main>
      <header>
        <p className="kicker">屏幕到相机的彩色条码流</p>
        <h1>MiraCode</h1>
        <p className="lead">
          颜色是第三维，连续播放的帧是第四维。下面这张图概括从选色、成帧、播放到拍摄还原的全过程。
        </p>
      </header>
      <section className="panel">
        <h2>全过程</h2>
        <div className="diagram" ref={diagramRef} aria-label="MiraCode 流程图" />
      </section>
      <section className="panel play">
        <h2>试玩</h2>
        <label>
          要发送的文字
          <textarea value={text} onChange={(event) => setText(event.target.value)} rows={5} />
        </label>
        <label>
          颜色数
          <select value={colors} onChange={(event) => setColors(Number(event.target.value))}>
            <option value={8}>8 色</option>
            <option value={16}>16 色</option>
          </select>
        </label>
        <div className="actions">
          <button type="button" disabled={busy} onClick={() => void generate()}>
            生成视频
          </button>
          <label className="file">
            解码视频
            <input
              type="file"
              accept="video/avi,.avi"
              disabled={busy}
              onChange={(event) => {
                const file = event.target.files?.[0];
                if (file) void decodeFile(file);
              }}
            />
          </label>
          {download ? (
            <a href={download} download="miracode.avi">
              下载 AVI
            </a>
          ) : null}
        </div>
        <p className="status">{status}</p>
        <canvas ref={canvasRef} />
        {frameLabel ? <p className="meta">{frameLabel}</p> : null}
        <label>
          解码结果
          <textarea value={decoded} readOnly rows={5} />
        </label>
      </section>
    </main>
  );
}
