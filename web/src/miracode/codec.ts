import { ReedSolomon } from "./reedsolomon";

export class HueClassifier {
  static inSector(hue: number, start: number, end: number): boolean {
    hue = (hue % 360 + 360) % 360;
    start = (start % 360 + 360) % 360;
    end = (end % 360 + 360) % 360;
    if (start < end) return start < hue && hue <= end;
    if (start > end) return hue > start || hue <= end;
    return false;
  }

  static classify(hue: number, bounds: number[]): number {
    for (let index = 0; index < bounds.length; index += 1) {
      const start = bounds[(index - 1 + bounds.length) % bounds.length];
      if (this.inSector(hue, start, bounds[index])) return index;
    }
    const wrapped = (hue % 360 + 360) % 360;
    let best = 0;
    let bestDist = 360;
    bounds.forEach((bound, index) => {
      const delta = Math.min((wrapped - bound + 360) % 360, (bound - wrapped + 360) % 360);
      if (delta < bestDist) {
        bestDist = delta;
        best = index;
      }
    });
    return best;
  }
}

export class SymbolCodec {
  static readonly infoPayloadBytes = 6;
  static readonly infoParity = 4;
  static readonly rsData = 32;
  static readonly rsParity = 16;
  static readonly rsBlock = 48;

  readonly bits: number;
  private readonly dataCode = new ReedSolomon(SymbolCodec.rsParity);
  private readonly infoCode = new ReedSolomon(SymbolCodec.infoParity);

  constructor(readonly nColors: number) {
    this.bits = SymbolCodec.bitsPerSymbol(nColors);
  }

  static bitsPerSymbol(nColors: number): number {
    const bits = Math.round(Math.log2(nColors));
    if (2 ** bits !== nColors) throw new Error("颜色数必须是 2 的幂");
    return bits;
  }

  mask(symbols: number[], undo = false): number[] {
    return symbols.map((symbol, index) => {
      const delta = (index * 17 + 3) % this.nColors;
      return undo ? (symbol - delta + this.nColors) % this.nColors : (symbol + delta) % this.nColors;
    });
  }

  payloadCapacity(symbolCount: number): number {
    const raw = Math.floor((symbolCount * this.bits) / 8);
    if (raw % SymbolCodec.rsBlock !== 0) throw new Error("版面字节数无法排满 RS 短码字");
    return (raw / SymbolCodec.rsBlock) * SymbolCodec.rsData;
  }

  encodeData(chunk: Uint8Array, symbolCount: number): number[] {
    const capacity = this.payloadCapacity(symbolCount);
    if (chunk.length > capacity) throw new Error("单帧数据超过容量");
    const body = new Uint8Array(capacity);
    body.set(chunk);
    const parts: Uint8Array[] = [];
    for (let offset = 0; offset < body.length; offset += SymbolCodec.rsData) {
      parts.push(this.dataCode.encode(body.subarray(offset, offset + SymbolCodec.rsData)));
    }
    const coded = concatBytes(parts);
    return this.mask(this.bytesToSymbols(coded, symbolCount));
  }

  decodeData(symbols: number[], length: number): Uint8Array {
    const raw = Math.floor((symbols.length * this.bits) / 8);
    const coded = this.symbolsToBytes(this.mask(symbols, true), raw);
    const parts: Uint8Array[] = [];
    for (let offset = 0; offset < coded.length; offset += SymbolCodec.rsBlock) {
      parts.push(this.dataCode.decode(coded.subarray(offset, offset + SymbolCodec.rsBlock)));
    }
    const body = concatBytes(parts);
    if (length > body.length) throw new Error("帧信息里的长度超出本帧容量");
    return body.subarray(0, length);
  }

  encodeFrameInfo(total: number, index: number, length: number): number[] {
    if (!(index >= 0 && index < total && total <= 65535 && length >= 0 && length <= 65535)) {
      throw new Error("帧号或长度超出帧信息字段");
    }
    const payload = new Uint8Array(6);
    const view = new DataView(payload.buffer);
    view.setUint16(0, total);
    view.setUint16(2, index);
    view.setUint16(4, length);
    const coded = this.infoCode.encode(payload);
    const symbols: number[] = [];
    coded.forEach((byte) => {
      [6, 4, 2, 0].forEach((shift) => symbols.push((byte >> shift) & 0x3));
    });
    return symbols;
  }

  decodeFrameInfo(symbols: number[]): { total: number; index: number; length: number } {
    const needed = (SymbolCodec.infoPayloadBytes + SymbolCodec.infoParity) * 4;
    if (symbols.length < needed) throw new Error("帧信息色块不够");
    const out = new Uint8Array(needed / 4);
    for (let offset = 0; offset < needed; offset += 4) {
      let byte = 0;
      for (let i = 0; i < 4; i += 1) byte = (byte << 2) | symbols[offset + i];
      out[offset / 4] = byte;
    }
    const plain = this.infoCode.decode(out);
    const view = new DataView(plain.buffer, plain.byteOffset, plain.byteLength);
    return { total: view.getUint16(0), index: view.getUint16(2), length: view.getUint16(4) };
  }

  private bytesToSymbols(data: Uint8Array, count: number): number[] {
    const symbols: number[] = [];
    let buffer = 0;
    let filled = 0;
    data.forEach((byte) => {
      buffer = (buffer << 8) | byte;
      filled += 8;
      while (filled >= this.bits) {
        filled -= this.bits;
        symbols.push((buffer >> filled) & ((1 << this.bits) - 1));
      }
    });
    while (symbols.length < count) symbols.push(0);
    if (symbols.length !== count) throw new Error("符号个数超出版面");
    return symbols;
  }

  private symbolsToBytes(symbols: number[], nbytes: number): Uint8Array {
    const out = new Uint8Array(nbytes);
    let buffer = 0;
    let filled = 0;
    let written = 0;
    for (const symbol of symbols) {
      buffer = (buffer << this.bits) | symbol;
      filled += this.bits;
      while (filled >= 8 && written < nbytes) {
        filled -= 8;
        out[written] = (buffer >> filled) & 0xff;
        written += 1;
      }
    }
    if (written < nbytes) throw new Error("色块不足以还原字节");
    return out;
  }
}

function concatBytes(parts: Uint8Array[]): Uint8Array {
  const total = parts.reduce((sum, part) => sum + part.length, 0);
  const out = new Uint8Array(total);
  let offset = 0;
  parts.forEach((part) => {
    out.set(part, offset);
    offset += part.length;
  });
  return out;
}
