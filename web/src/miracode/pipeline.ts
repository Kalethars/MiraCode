import { HueClassifier, SymbolCodec } from "./codec";
import { DecodeError, FrameLocator, MixedFrame, mapPoints } from "./finder";
import { FramePainter, Geometry, RgbImage } from "./layout";
import { meanHue, measuredPalette } from "./palette";

export interface DecodedFrame {
  index: number;
  total: number;
  payload: Uint8Array;
}

function circularMean(hues: number[]): number {
  let sin = 0;
  let cos = 0;
  hues.forEach((hue) => {
    const rad = (hue * Math.PI) / 180;
    sin += Math.sin(rad);
    cos += Math.cos(rad);
  });
  return ((Math.atan2(sin / hues.length, cos / hues.length) * 180) / Math.PI + 360) % 360;
}

export class MiraCode {
  readonly coding: number[];
  readonly bounds: number[];
  readonly geometry: Geometry;
  readonly codec: SymbolCodec;
  readonly painter: FramePainter;
  readonly locator: FrameLocator;

  constructor(readonly nColors = 16) {
    const palette = measuredPalette(nColors);
    this.coding = palette.coding;
    this.bounds = palette.bounds;
    this.geometry = new Geometry(nColors);
    this.codec = new SymbolCodec(nColors);
    this.painter = new FramePainter(this.geometry);
    this.locator = new FrameLocator(this.geometry);
  }

  encode(payload: Uint8Array): RgbImage[] {
    const capacity = this.codec.payloadCapacity(this.geometry.dataSymbolCount);
    const chunks: Uint8Array[] = [];
    if (payload.length === 0) chunks.push(new Uint8Array());
    else {
      for (let offset = 0; offset < payload.length; offset += capacity) {
        chunks.push(payload.subarray(offset, offset + capacity));
      }
    }
    return chunks.map((chunk, index) => {
      const data = this.codec.encodeData(chunk, this.geometry.dataSymbolCount);
      const info = this.codec.encodeFrameInfo(chunks.length, index, chunk.length);
      return this.painter.render(data, info, this.coding, this.bounds, index);
    });
  }

  decodeFrame(image: RgbImage): DecodedFrame {
    const { transform } = this.locator.locate(image);
    const info = this.readFrameInfo(image, transform);
    const { total, index, length } = this.codec.decodeFrameInfo(info);
    const bounds = this.readPalette(image, transform);
    const symbols = this.readData(image, transform, bounds);
    return { index, total, payload: this.codec.decodeData(symbols, length) };
  }

  decode(frames: RgbImage[]): Uint8Array {
    const parts = new Map<number, Uint8Array>();
    let total: number | null = null;
    frames.forEach((image) => {
      try {
        const frame = this.decodeFrame(image);
        if (total === null) total = frame.total;
        else if (frame.total !== total) throw new DecodeError("各帧记录的总帧数不一致");
        parts.set(frame.index, frame.payload);
      } catch (error) {
        if (error instanceof MixedFrame) return;
        throw error;
      }
    });
    if (total === null) throw new DecodeError("没有可解码的帧");
    const missing = [];
    for (let index = 0; index < total; index += 1) if (!parts.has(index)) missing.push(index);
    if (missing.length) throw new DecodeError(`缺少帧 ${missing.join(", ")}`);
    const pieces = Array.from({ length: total }, (_, index) => parts.get(index)!);
    const size = pieces.reduce((sum, piece) => sum + piece.length, 0);
    const out = new Uint8Array(size);
    let offset = 0;
    pieces.forEach((piece) => {
      out.set(piece, offset);
      offset += piece.length;
    });
    return out;
  }

  private sampleHue(image: RgbImage, x: number, y: number): number {
    return meanHue(image.patch(x, y, 3));
  }

  private readPalette(image: RgbImage, transform: number[][]): number[] {
    const geom = this.geometry;
    const points: [number, number][] = [];
    const owners: number[] = [];
    for (let row = 0; row < geom.dataRows; row += 1) {
      const colorIndex = row % geom.nColors;
      [geom.leftPaletteX, geom.rightPaletteX].forEach((moduleX) => {
        points.push(geom.moduleCenter(moduleX, geom.dataY + row));
        owners.push(colorIndex);
      });
    }
    const mapped = mapPoints(transform, points);
    const acc = Array.from({ length: geom.nColors }, () => [] as number[]);
    mapped.forEach(([x, y], index) => acc[owners[index]].push(this.sampleHue(image, x, y)));
    return acc.map((hues) => {
      if (!hues.length) throw new DecodeError("色板不完整");
      return circularMean(hues);
    });
  }

  private readData(image: RgbImage, transform: number[][], bounds: number[]): number[] {
    const geom = this.geometry;
    const points: [number, number][] = [];
    for (let row = 0; row < geom.dataRows; row += 1) {
      for (let col = 0; col < geom.dataCols; col += 1) points.push(geom.moduleCenter(geom.dataX + col, geom.dataY + row));
    }
    return mapPoints(transform, points).map(([x, y]) => HueClassifier.classify(this.sampleHue(image, x, y), bounds));
  }

  private readFrameInfo(image: RgbImage, transform: number[][]): number[] {
    const geom = this.geometry;
    const swatches = mapPoints(
      transform,
      [0, 1, 2, 3].map((index) => geom.moduleCenter(0, geom.dataY + index)),
    );
    const hues = swatches.map(([x, y]) => this.sampleHue(image, x, y));
    const bounds = hues.map((hue, index) => {
      const next = hues[(index + 1) % 4];
      return (hue + ((next - hue + 360) % 360) / 2) % 360;
    });
    const count = (SymbolCodec.infoPayloadBytes + SymbolCodec.infoParity) * 4;
    const points: [number, number][] = [];
    for (let index = 0; index < count; index += 1) {
      const row = Math.floor(index / geom.infoCols);
      const col = index % geom.infoCols;
      points.push(geom.moduleCenter(geom.infoX + col, geom.dataY + row));
    }
    return mapPoints(transform, points).map(([x, y]) => HueClassifier.classify(this.sampleHue(image, x, y), bounds));
  }
}
