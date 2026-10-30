export const HUE64 = [
  0.05, 12.49, 19.87, 25.76, 31.02, 35.91, 40.59, 45.18, 49.76, 54.51, 59.78, 65.2, 70.02, 74.37,
  78.53, 82.51, 86.37, 90.4, 94.95, 100.33, 106.66, 123.21, 134.51, 140.03, 144.56, 148.67, 152.52,
  156.11, 159.72, 163.58, 168.16, 173.81, 180, 185.34, 189.88, 194.14, 198.9, 204.67, 210.83, 217.16,
  224.87, 242.95, 259.28, 265.12, 269.6, 273.71, 277.75, 281.66, 285.49, 289.3, 293.3, 297.58, 302.12,
  306.64, 311.05, 315.35, 319.55, 323.74, 327.95, 332.14, 336.42, 341.03, 346.36, 352.67,
] as const;

export const FRAME_HUES = [0, 90, 180, 270];

export function measuredPalette(n: number): { coding: number[]; bounds: number[] } {
  if (64 % n !== 0) throw new Error("颜色数量必须能整除 64");
  const step = 64 / n;
  const coding = Array.from({ length: n }, (_, i) => HUE64[i * step]);
  let bounds: number[];
  if (64 % (2 * n) === 0) {
    const half = 64 / (2 * n);
    bounds = Array.from({ length: n }, (_, i) => HUE64[(2 * i + 1) * half]);
  } else {
    bounds = coding.map((hue, i) => {
      const span = (coding[(i + 1) % n] - hue + 360) % 360;
      return (hue + span / 2) % 360;
    });
  }
  return { coding, bounds };
}

export function hueToRgb(hue: number): [number, number, number] {
  const h = ((hue % 360) + 360) % 360 / 60;
  const c = 1;
  const x = 1 - Math.abs((h % 2) - 1);
  const sector = Math.floor(h) % 6;
  const table: [number, number, number][] = [
    [c, x, 0],
    [x, c, 0],
    [0, c, x],
    [0, x, c],
    [x, 0, c],
    [c, 0, x],
  ];
  const [r, g, b] = table[sector];
  return [Math.round(r * 255), Math.round(g * 255), Math.round(b * 255)];
}

export function rgbToHsv(r: number, g: number, b: number): [number, number, number] {
  const rn = r / 255;
  const gn = g / 255;
  const bn = b / 255;
  const max = Math.max(rn, gn, bn);
  const min = Math.min(rn, gn, bn);
  const d = max - min;
  let h = 0;
  if (d > 1e-8) {
    if (max === rn) h = ((gn - bn) / d) % 6;
    else if (max === gn) h = (bn - rn) / d + 2;
    else h = (rn - gn) / d + 4;
  }
  const hue = ((h / 6) % 1) * 360;
  const sat = max > 1e-8 ? d / max : 0;
  return [hue < 0 ? hue + 360 : hue, sat, max];
}

export function meanHue(pixels: Uint8ClampedArray, saturationMin = 0.35): number {
  let sin = 0;
  let cos = 0;
  let count = 0;
  for (let i = 0; i < pixels.length; i += 3) {
    const [hue, sat] = rgbToHsv(pixels[i], pixels[i + 1], pixels[i + 2]);
    if (sat < saturationMin) continue;
    const rad = (hue * Math.PI) / 180;
    sin += Math.sin(rad);
    cos += Math.cos(rad);
    count += 1;
  }
  if (count === 0) return 0;
  return ((Math.atan2(sin / count, cos / count) * 180) / Math.PI + 360) % 360;
}
