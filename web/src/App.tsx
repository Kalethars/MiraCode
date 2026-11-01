import { useEffect, useRef, useState } from "react";
import mermaid from "mermaid";
import { FLOW } from "./diagram";
import { MiraCode } from "./miracode/pipeline";
import { RgbImage } from "./miracode/layout";
import { readAvi, writeAvi } from "./miracode/video";

const SAMPLE_IMAGE = "https://interactive-examples.mdn.mozilla.net/media/cc0-images/grapefruit-slice-332-332.jpg";
const SAMPLE_VIDEO = "https://interactive-examples.mdn.mozilla.net/media/cc0-videos/flower.webm";
const FPS = 10;

type SourceId = "text" | "file" | "image" | "video";

function bytesPerFrame(colors: number): number {
  const bits = Math.log2(colors);
  return Math.round((1888 * bits) / 8);
}

function transmissionSeconds(byteLength: number, colors: number): number {
  const frames = Math.max(1, Math.ceil(byteLength / bytesPerFrame(colors)));
  return frames / FPS;
}

mermaid.initialize({
  startOnLoad: false,
  securityLevel: "strict",
  theme: "base",
  flowchart: { htmlLabels: true, curve: "linear", padding: 12, nodeSpacing: 28, rankSpacing: 28 },
  themeVariables: {
    fontFamily: '"Segoe UI", "PingFang SC", "Noto Sans SC", sans-serif',
    fontSize: "15px",
    primaryColor: "#fffdf8",
    primaryTextColor: "#241f19",
    primaryBorderColor: "#c9b99d",
    lineColor: "#8a7a63",
    textColor: "#241f19",
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
  const [source, setSource] = useState<SourceId>("text");
  const [file, setFile] = useState<{ name: string; bytes: Uint8Array; preview: string | null; kind: "image" | "video" | "other" } | null>(null);
  const [samples, setSamples] = useState<{ image: Uint8Array | null; video: Uint8Array | null }>({ image: null, video: null });
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

  useEffect(() => {
    let cancelled = false;
    async function load(url: string): Promise<Uint8Array> {
      const response = await fetch(url);
      if (!response.ok) throw new Error(String(response.status));
      return new Uint8Array(await response.arrayBuffer());
    }
    load(SAMPLE_IMAGE).then((image) => {
      if (!cancelled) setSamples((current) => ({ ...current, image }));
    }).catch(() => undefined);
    load(SAMPLE_VIDEO).then((video) => {
      if (!cancelled) setSamples((current) => ({ ...current, video }));
    }).catch(() => undefined);
    return () => {
      cancelled = true;
    };
  }, []);

  function takeFile(next: File): void {
    const kind = next.type.startsWith("image/") ? "image" : next.type.startsWith("video/") ? "video" : "other";
    const preview = kind === "other" ? null : URL.createObjectURL(next);
    next.arrayBuffer().then((buffer) => {
      setFile((previous) => {
        if (previous?.preview) URL.revokeObjectURL(previous.preview);
        return { name: next.name, bytes: new Uint8Array(buffer), preview, kind };
      });
      setSource("file");
    });
  }

  function payload(): Uint8Array | null {
    if (source === "text") return new TextEncoder().encode(text);
    if (source === "file") return file?.bytes ?? null;
    if (source === "image") return samples.image;
    return samples.video;
  }

  async function generate(): Promise<void> {
    setBusy(true);
    const body = payload();
    if (!body) {
      setStatus(source === "file" ? "先选择要发送的文件。" : "示例还在下载。");
      setBusy(false);
      return;
    }
    setStatus("正在编成彩色帧…");
    await new Promise((resolve) => setTimeout(resolve, 30));
    try {
      const frames = new MiraCode(colors).encode(body);
      const avi = writeAvi(frames, 10);
      const url = URL.createObjectURL(new Blob([avi], { type: "video/avi" }));
      setDownload((previous) => {
        if (previous) URL.revokeObjectURL(previous);
        return url;
      });
      if (canvasRef.current) paint(canvasRef.current, frames[0]);
      setFrameLabel(`共 ${frames.length} 帧，预览第 1 帧。每帧 ${frames[0].width}×${frames[0].height} 像素。`);
      setStatus("已生成无压缩 AVI。浏览器通常不能直接播放这种视频，请下载后用解码还原。");
    } catch (error) {
      setStatus(error instanceof Error ? error.message : "生成失败");
    } finally {
      setBusy(false);
    }
  }

  async function decodeFile(next: File): Promise<void> {
    setBusy(true);
    setStatus("正在读取视频并定位每一帧…");
    await new Promise((resolve) => setTimeout(resolve, 30));
    try {
      const bytes = new Uint8Array(await next.arrayBuffer());
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
          颜色是第三维，连续播放的帧是第四维。论文给出的容量：16 色、色块识别率 100%、1888 个数据色块时，每帧 944 字节。按 10 帧/秒播放，传输速率为 75.5 kbit/s。
        </p>
      </header>
      <div className="workspace">
        <aside className="panel">
          <h2>全过程</h2>
          <div className="diagram" ref={diagramRef} aria-label="MiraCode 流程图" />
        </aside>
        <section className="panel play">
          <h2>试玩</h2>
          <div className="choices" role="radiogroup" aria-label="发送内容，四选一">
            {(["text", "file", "image", "video"] as const).map((id) => (
              <label key={id} className={source === id ? "choice on" : "choice"}>
                <input type="radio" name="source" checked={source === id} onChange={() => setSource(id)} />
                {id === "text" ? "文字" : id === "file" ? "上传文件" : id === "image" ? "示例图片" : "示例视频"}
              </label>
            ))}
          </div>
          {source === "text" ? (
            <label className="field">
              要发送的文字
              <textarea value={text} onChange={(event) => setText(event.target.value)} rows={5} />
            </label>
          ) : null}
          {source === "file" ? (
            <div className="field">
              <label className="btn">
                选择文件
                <input
                  type="file"
                  disabled={busy}
                  onChange={(event) => {
                    const next = event.target.files?.[0];
                    if (next) takeFile(next);
                    event.target.value = "";
                  }}
                />
              </label>
              {file?.kind === "image" && file.preview ? <img className="source" src={file.preview} alt={file.name} /> : null}
              {file?.kind === "video" && file.preview ? <video className="source" src={file.preview} controls /> : null}
              <p className="meta file-name">{file ? `${file.name} · ${file.bytes.length} 字节` : "还没有选择文件。"}</p>
            </div>
          ) : null}
          <div className="previews">
            <figure className={source === "image" ? "preview on" : "preview"} onClick={() => setSource("image")}>
              <figcaption>示例图片</figcaption>
              <img src={SAMPLE_IMAGE} alt="示例图片：一瓣葡萄柚" />
            </figure>
            <figure className={source === "video" ? "preview on" : "preview"} onClick={() => setSource("video")}>
              <figcaption>示例视频</figcaption>
              <video src={SAMPLE_VIDEO} controls />
            </figure>
          </div>
          <p className="eta">
            {payload()
              ? `预计传输 ${transmissionSeconds(payload()!.length, colors).toFixed(1)} 秒`
              : "预计传输 — 秒"}
            {`（论文速率，${colors} 色每帧 ${bytesPerFrame(colors)} 字节，${FPS} 帧/秒）`}
          </p>
          <label className="field">
            颜色数
            <select value={colors} onChange={(event) => setColors(Number(event.target.value))}>
              <option value={8}>8 色</option>
              <option value={16}>16 色</option>
            </select>
          </label>
          <div className="actions">
            <button type="button" className="btn solid" disabled={busy} onClick={() => void generate()}>
              生成视频
            </button>
            <label className="btn">
              解码视频
              <input
                type="file"
                accept="video/avi,.avi"
                disabled={busy}
                onChange={(event) => {
                  const next = event.target.files?.[0];
                  if (next) void decodeFile(next);
                  event.target.value = "";
                }}
              />
            </label>
            {download ? (
              <a className="btn" href={download} download="miracode.avi">
                下载 AVI
              </a>
            ) : null}
          </div>
          <p className="status">{status}</p>
          <canvas ref={canvasRef} />
          {frameLabel ? <p className="meta">{frameLabel}</p> : null}
          <label className="field">
            解码结果
            <textarea value={decoded} readOnly rows={5} />
          </label>
        </section>
      </div>
    </main>
  );
}
