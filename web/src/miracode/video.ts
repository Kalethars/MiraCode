import { RgbImage } from "./layout";

function chunk(tag: string, payload: Uint8Array): Uint8Array {
  const pad = payload.length % 2 ? 1 : 0;
  const out = new Uint8Array(8 + payload.length + pad);
  out.set(new TextEncoder().encode(tag));
  new DataView(out.buffer).setUint32(4, payload.length, true);
  out.set(payload, 8);
  return out;
}

function list(kind: string, payload: Uint8Array): Uint8Array {
  const body = new Uint8Array(4 + payload.length);
  body.set(new TextEncoder().encode(kind));
  body.set(payload, 4);
  return chunk("LIST", body);
}

function concat(parts: Uint8Array[]): Uint8Array {
  const total = parts.reduce((sum, part) => sum + part.length, 0);
  const out = new Uint8Array(total);
  let offset = 0;
  parts.forEach((part) => {
    out.set(part, offset);
    offset += part.length;
  });
  return out;
}

function frameBlob(frame: RgbImage): Uint8Array {
  const stride = (frame.width * 3 + 3) & ~3;
  const out = new Uint8Array(frame.height * stride);
  for (let y = 0; y < frame.height; y += 1) {
    const src = (frame.height - 1 - y) * frame.width * 3;
    const dst = y * stride;
    for (let x = 0; x < frame.width; x += 1) {
      out[dst + x * 3] = frame.data[src + x * 3 + 2];
      out[dst + x * 3 + 1] = frame.data[src + x * 3 + 1];
      out[dst + x * 3 + 2] = frame.data[src + x * 3];
    }
  }
  return out;
}

export function writeAvi(frames: RgbImage[], fps = 10): Uint8Array {
  if (!frames.length) throw new Error("没有帧可以写入");
  if (fps <= 0) throw new Error("帧率必须为正");
  const blobs = frames.map(frameBlob);
  const { width, height } = frames[0];
  if (frames.some((frame) => frame.width !== width || frame.height !== height)) throw new Error("各帧尺寸不一致");
  const frameSize = blobs[0].length;
  const avih = new Uint8Array(56);
  const avihView = new DataView(avih.buffer);
  const avihValues = [
    Math.floor(1_000_000 / fps),
    frameSize * fps,
    0,
    0,
    frames.length,
    0,
    1,
    frameSize,
    width,
    height,
    0,
    0,
    0,
    0,
  ];
  avihValues.forEach((value, index) => avihView.setUint32(index * 4, value, true));
  const strh = new Uint8Array(56);
  strh.set(new TextEncoder().encode("vidsDIB "));
  const strhView = new DataView(strh.buffer);
  strhView.setUint32(8, 0, true);
  strhView.setUint16(12, 0, true);
  strhView.setUint16(14, 0, true);
  strhView.setUint32(16, 0, true);
  strhView.setUint32(20, 1, true);
  strhView.setUint32(24, fps, true);
  strhView.setUint32(28, 0, true);
  strhView.setUint32(32, frames.length, true);
  strhView.setUint32(36, frameSize, true);
  strhView.setUint32(40, 0xffffffff, true);
  strhView.setUint32(44, 0, true);
  strhView.setInt16(48, 0, true);
  strhView.setInt16(50, 0, true);
  strhView.setInt16(52, width, true);
  strhView.setInt16(54, height, true);
  const strf = new Uint8Array(40);
  const strfView = new DataView(strf.buffer);
  strfView.setUint32(0, 40, true);
  strfView.setInt32(4, width, true);
  strfView.setInt32(8, height, true);
  strfView.setUint16(12, 1, true);
  strfView.setUint16(14, 24, true);
  strfView.setUint32(16, 0, true);
  strfView.setUint32(20, frameSize, true);
  const hdrl = list("hdrl", concat([chunk("avih", avih), list("strl", concat([chunk("strh", strh), chunk("strf", strf)]))]));
  const movi = chunk("LIST", concat([new TextEncoder().encode("movi"), ...blobs.map((blob) => chunk("00db", blob))]));
  const body = concat([hdrl, movi]);
  const avi = new Uint8Array(12 + body.length);
  avi.set(new TextEncoder().encode("RIFF"));
  new DataView(avi.buffer).setUint32(4, 4 + body.length, true);
  avi.set(new TextEncoder().encode("AVI "), 8);
  avi.set(body, 12);
  return avi;
}

function findAscii(data: Uint8Array, text: string, from = 0): number {
  const needle = new TextEncoder().encode(text);
  for (let i = from; i <= data.length - needle.length; i += 1) {
    let match = true;
    for (let j = 0; j < needle.length; j += 1) {
      if (data[i + j] !== needle[j]) {
        match = false;
        break;
      }
    }
    if (match) return i;
  }
  return -1;
}

export function readAvi(data: Uint8Array): RgbImage[] {
  const head = new TextDecoder().decode(data.subarray(0, 12));
  if (!head.startsWith("RIFF") || head.slice(8, 12) !== "AVI ") throw new Error("不是 AVI 文件");
  const strfAt = findAscii(data, "strf");
  if (strfAt < 0) throw new Error("AVI 缺少位图头");
  const header = new DataView(data.buffer, data.byteOffset + strfAt + 8, 40);
  const width = header.getInt32(4, true);
  const height = header.getInt32(8, true);
  const bitCount = header.getUint16(14, true);
  if (bitCount !== 24) throw new Error("只读取 24 位无压缩 AVI");
  const absHeight = Math.abs(height);
  const stride = (width * 3 + 3) & ~3;
  const frames: RgbImage[] = [];
  let cursor = 12;
  while (true) {
    const at = findAscii(data, "00db", cursor);
    if (at < 0) break;
    const size = new DataView(data.buffer, data.byteOffset + at + 4, 4).getUint32(0, true);
    const raw = data.subarray(at + 8, at + 8 + size);
    if (raw.length < absHeight * stride) break;
    const image = new RgbImage(width, absHeight);
    for (let y = 0; y < absHeight; y += 1) {
      const src = (absHeight - 1 - y) * stride;
      const dst = y * width * 3;
      for (let x = 0; x < width; x += 1) {
        image.data[dst + x * 3] = raw[src + x * 3 + 2];
        image.data[dst + x * 3 + 1] = raw[src + x * 3 + 1];
        image.data[dst + x * 3 + 2] = raw[src + x * 3];
      }
    }
    frames.push(image);
    cursor = at + 8 + size + (size % 2);
  }
  if (!frames.length) throw new Error("AVI 里没有视频帧");
  return frames;
}
