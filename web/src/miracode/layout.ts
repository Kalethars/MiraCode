import { FRAME_HUES, hueToRgb } from "./palette";

const MODULE = 16;
const FINDER = 6;
const SPECIAL = 72;
const RED: [number, number, number] = [255, 0, 0];
const GREEN: [number, number, number] = [0, 255, 0];

export class Geometry {
  readonly leftPaletteX: number;
  readonly leftAlignX: number;
  readonly infoX: number;
  readonly dataX: number;
  readonly rightAlignX: number;
  readonly rightPaletteX: number;
  readonly rightFinderX: number;
  readonly topAlignY: number;
  readonly dataY: number;
  readonly bottomAlignY: number;
  readonly bottomFinderY: number;
  readonly widthModules: number;
  readonly heightModules: number;

  constructor(
    readonly nColors: number,
    readonly module = MODULE,
    readonly margin = 1,
    readonly finder = FINDER,
    readonly dataRows = nColors > 32 ? 64 : 32,
    readonly dataCols = 24,
    readonly infoCols = 2,
  ) {
    this.leftPaletteX = margin + finder;
    this.leftAlignX = this.leftPaletteX + 1;
    this.infoX = this.leftAlignX + 1;
    this.dataX = this.infoX + infoCols;
    this.rightAlignX = this.dataX + dataCols;
    this.rightPaletteX = this.rightAlignX + 1;
    this.rightFinderX = this.rightPaletteX + 1;
    this.topAlignY = margin + finder;
    this.dataY = this.topAlignY + 1;
    this.bottomAlignY = this.dataY + dataRows;
    this.bottomFinderY = this.bottomAlignY + 1;
    this.widthModules = this.rightFinderX + finder + margin;
    this.heightModules = this.bottomFinderY + finder + margin;
  }

  get dataSymbolCount(): number {
    return this.dataRows * this.dataCols;
  }

  moduleCenter(moduleX: number, moduleY: number): [number, number] {
    return [(moduleX + 0.5) * this.module, (moduleY + 0.5) * this.module];
  }

  designCorners(): [number, number][] {
    const slot = (x: number, y: number): [number, number] => {
      const side = this.finder * this.module;
      return [x * this.module + side / 2, y * this.module + side / 2];
    };
    return [
      slot(this.margin, this.margin),
      slot(this.rightFinderX, this.margin),
      slot(this.rightFinderX, this.bottomFinderY),
      slot(this.margin, this.bottomFinderY),
    ];
  }
}

export class RgbImage {
  constructor(
    readonly width: number,
    readonly height: number,
    readonly data = new Uint8ClampedArray(width * height * 3).fill(255),
  ) {}

  fill(x: number, y: number, w: number, h: number, color: [number, number, number]): void {
    const x1 = Math.max(0, x);
    const y1 = Math.max(0, y);
    const x2 = Math.min(this.width, x + w);
    const y2 = Math.min(this.height, y + h);
    for (let row = y1; row < y2; row += 1) {
      for (let col = x1; col < x2; col += 1) {
        const i = (row * this.width + col) * 3;
        this.data[i] = color[0];
        this.data[i + 1] = color[1];
        this.data[i + 2] = color[2];
      }
    }
  }

  patch(x: number, y: number, radius: number): Uint8ClampedArray {
    const xi = Math.round(x);
    const yi = Math.round(y);
    const x0 = Math.max(0, xi - radius);
    const x1 = Math.min(this.width, xi + radius + 1);
    const y0 = Math.max(0, yi - radius);
    const y1 = Math.min(this.height, yi + radius + 1);
    const out = new Uint8ClampedArray((x1 - x0) * (y1 - y0) * 3);
    let cursor = 0;
    for (let row = y0; row < y1; row += 1) {
      for (let col = x0; col < x1; col += 1) {
        const i = (row * this.width + col) * 3;
        out[cursor] = this.data[i];
        out[cursor + 1] = this.data[i + 1];
        out[cursor + 2] = this.data[i + 2];
        cursor += 3;
      }
    }
    return out;
  }
}

function drawFinder(image: RgbImage, x: number, y: number, side: number, ring: [number, number, number]): void {
  image.fill(x, y, side, side, [0, 0, 0]);
  const unit = Math.floor(side / 6);
  image.fill(x + unit, y + unit, side - 2 * unit, side - 2 * unit, ring);
  const inner = 2 * unit;
  image.fill(x + inner, y + inner, side - 2 * inner, side - 2 * inner, [0, 0, 0]);
}

export class FramePainter {
  constructor(readonly geometry: Geometry) {}

  render(dataSymbols: number[], infoSymbols: number[], coding: number[], bounds: number[], frameIndex: number): RgbImage {
    const geom = this.geometry;
    if (dataSymbols.length !== geom.dataSymbolCount) throw new Error("数据符号数量与版面不一致");
    const image = new RgbImage(geom.widthModules * geom.module, geom.heightModules * geom.module);
    const ring = frameIndex % 2 === 0 ? RED : GREEN;
    const normal = geom.finder * geom.module;
    const offset = Math.floor((normal - SPECIAL) / 2);
    const slots: [number, number, boolean][] = [
      [geom.margin, geom.margin, true],
      [geom.rightFinderX, geom.margin, false],
      [geom.margin, geom.bottomFinderY, false],
      [geom.rightFinderX, geom.bottomFinderY, false],
    ];
    slots.forEach(([mx, my, special]) => {
      const px = mx * geom.module;
      const py = my * geom.module;
      if (special) drawFinder(image, px + offset, py + offset, SPECIAL, ring);
      else drawFinder(image, px, py, normal, ring);
    });
    for (let col = 0; col < geom.dataCols; col += 1) {
      const color: [number, number, number] = col % 2 === 0 ? [0, 0, 0] : [255, 255, 255];
      this.fillModule(image, geom.dataX + col, geom.topAlignY, color);
      this.fillModule(image, geom.dataX + col, geom.bottomAlignY, color);
    }
    for (let row = 0; row < geom.dataRows; row += 1) {
      const color: [number, number, number] = row % 2 === 0 ? [0, 0, 0] : [255, 255, 255];
      this.fillModule(image, geom.leftAlignX, geom.dataY + row, color);
      this.fillModule(image, geom.rightAlignX, geom.dataY + row, color);
      const swatch = hueToRgb(bounds[row % bounds.length]);
      this.fillModule(image, geom.leftPaletteX, geom.dataY + row, swatch);
      this.fillModule(image, geom.rightPaletteX, geom.dataY + row, swatch);
    }
    FRAME_HUES.forEach((hue, index) => this.fillModule(image, 0, geom.dataY + index, hueToRgb(hue)));
    infoSymbols.forEach((symbol, index) => {
      const row = Math.floor(index / geom.infoCols);
      const col = index % geom.infoCols;
      this.fillModule(image, geom.infoX + col, geom.dataY + row, hueToRgb(FRAME_HUES[symbol]));
    });
    dataSymbols.forEach((symbol, index) => {
      const row = Math.floor(index / geom.dataCols);
      const col = index % geom.dataCols;
      this.fillModule(image, geom.dataX + col, geom.dataY + row, hueToRgb(coding[symbol]));
    });
    return image;
  }

  private fillModule(image: RgbImage, moduleX: number, moduleY: number, color: [number, number, number]): void {
    const m = this.geometry.module;
    image.fill(moduleX * m, moduleY * m, m, m, color);
  }
}
