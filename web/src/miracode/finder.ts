import { RgbImage } from "./layout";

export class DecodeError extends Error {}
export class MixedFrame extends DecodeError {}

export interface FinderHit {
  y: number;
  x: number;
  width: number;
  votes: number;
}

interface Run {
  black: boolean;
  start: number;
  length: number;
}

function runsOf(line: boolean[]): Run[] {
  if (line.length === 0) return [];
  const runs: Run[] = [];
  let start = 0;
  for (let i = 1; i <= line.length; i += 1) {
    if (i === line.length || line[i] !== line[start]) {
      runs.push({ black: line[start], start, length: i - start });
      start = i;
    }
  }
  return runs;
}

function ratioOk(lengths: number[], tolerance = 0.45): { ok: boolean; total: number } {
  const total = lengths.reduce((sum, value) => sum + value, 0);
  const unit = total / 6;
  if (unit < 4) return { ok: false, total };
  const expected = [unit, unit, 2 * unit, unit, unit];
  const ok = lengths.every((length, i) => Math.abs(length - expected[i]) <= tolerance * unit);
  return { ok, total };
}

function verticalOk(mask: boolean[][], y: number, x: number, tolerance = 0.5): boolean {
  const height = mask.length;
  const width = mask[0]?.length ?? 0;
  if (x < 0 || x >= width) return false;
  const column = new Array<boolean>(height);
  for (let row = 0; row < height; row += 1) column[row] = mask[row][x];
  const runs = runsOf(column);
  for (let index = 0; index <= runs.length - 5; index += 1) {
    if (![0, 1, 2, 3, 4].every((k) => runs[index + k].black === (k % 2 === 0))) continue;
    const lengths = [0, 1, 2, 3, 4].map((k) => runs[index + k].length);
    const { ok } = ratioOk(lengths, tolerance);
    if (!ok) continue;
    const center = runs[index + 2].start + lengths[2] / 2;
    if (Math.abs(center - y) <= lengths[2]) return true;
  }
  return false;
}

function cluster(points: [number, number, number][], radius = 28): FinderHit[] {
  const groups: { y: number; x: number; ys: number[]; xs: number[]; ws: number[] }[] = [];
  points.forEach(([y, x, width]) => {
    const group = groups.find((item) => (y - item.y) ** 2 + (x - item.x) ** 2 <= radius ** 2);
    if (group) {
      group.ys.push(y);
      group.xs.push(x);
      group.ws.push(width);
      group.y = group.ys.reduce((sum, value) => sum + value, 0) / group.ys.length;
      group.x = group.xs.reduce((sum, value) => sum + value, 0) / group.xs.length;
    } else {
      groups.push({ y, x, ys: [y], xs: [x], ws: [width] });
    }
  });
  const hits: FinderHit[] = [];
  groups.forEach((group) => {
    if (group.ys.length < 4) return;
    const sorted = group.ws.slice().sort((a, b) => a - b);
    const mid = sorted.length >> 1;
    const width = sorted.length % 2 ? sorted[mid] : (sorted[mid - 1] + sorted[mid]) / 2;
    hits.push({ y: group.y, x: group.x, width, votes: group.ys.length });
  });
  hits.sort((a, b) => b.votes - a.votes);
  return hits;
}

export function findFinders(image: RgbImage): FinderHit[] {
  const height = image.height;
  const width = image.width;
  const mask: boolean[][] = new Array(height);
  for (let y = 0; y < height; y += 1) {
    const row = new Array<boolean>(width);
    const offset = y * width * 3;
    for (let x = 0; x < width; x += 1) {
      const i = offset + x * 3;
      row[x] = image.data[i] < 40 && image.data[i + 1] < 40 && image.data[i + 2] < 40;
    }
    mask[y] = row;
  }
  const points: [number, number, number][] = [];
  for (let y = 0; y < height; y += 1) {
    const runs = runsOf(mask[y]);
    for (let index = 0; index <= runs.length - 5; index += 1) {
      if (![0, 1, 2, 3, 4].every((k) => runs[index + k].black === (k % 2 === 0))) continue;
      const lengths = [0, 1, 2, 3, 4].map((k) => runs[index + k].length);
      const { ok, total } = ratioOk(lengths);
      if (!ok) continue;
      const centerX = runs[index + 2].start + lengths[2] / 2;
      if (verticalOk(mask, y, Math.round(centerX))) points.push([y, centerX, total]);
    }
  }
  return cluster(points);
}

export function orderCorners(hits: FinderHit[]): FinderHit[] {
  if (hits.length < 4) throw new DecodeError(`只找到 ${hits.length} 个定位图案`);
  const chosen = hits.slice().sort((a, b) => b.votes - a.votes).slice(0, 4);
  const special = chosen.reduce((best, hit) => (hit.width < best.width ? hit : best));
  const cy = chosen.reduce((sum, hit) => sum + hit.y, 0) / chosen.length;
  const cx = chosen.reduce((sum, hit) => sum + hit.x, 0) / chosen.length;
  const clockwise = chosen.slice().sort((a, b) => Math.atan2(a.y - cy, a.x - cx) - Math.atan2(b.y - cy, b.x - cx));
  const start = clockwise.indexOf(special);
  const ordered = [0, 1, 2, 3].map((offset) => clockwise[(start + offset) % 4]);
  const widths = ordered.map((hit) => hit.width).sort((a, b) => a - b);
  if (widths[0] > widths[1] * 0.9) throw new DecodeError("无法区分特殊定位图案");
  return ordered;
}

function solve8(matrix: number[][], target: number[]): number[] {
  const rows = matrix.map((row, i) => row.concat(target[i]));
  for (let col = 0; col < 8; col += 1) {
    let pivot = col;
    for (let row = col + 1; row < 8; row += 1) {
      if (Math.abs(rows[row][col]) > Math.abs(rows[pivot][col])) pivot = row;
    }
    [rows[col], rows[pivot]] = [rows[pivot], rows[col]];
    const scale = rows[col][col];
    if (Math.abs(scale) < 1e-12) throw new DecodeError("单应矩阵奇异");
    for (let index = col; index < 9; index += 1) rows[col][index] /= scale;
    for (let row = 0; row < 8; row += 1) {
      if (row === col) continue;
      const factor = rows[row][col];
      for (let index = col; index < 9; index += 1) rows[row][index] -= factor * rows[col][index];
    }
  }
  return rows.map((row) => row[8]);
}

export function homography(design: [number, number][], image: [number, number][]): number[][] {
  const matrix: number[][] = [];
  const target: number[] = [];
  design.forEach(([x, y], index) => {
    const [u, v] = image[index];
    matrix.push([x, y, 1, 0, 0, 0, -u * x, -u * y]);
    matrix.push([0, 0, 0, x, y, 1, -v * x, -v * y]);
    target.push(u, v);
  });
  const coeffs = solve8(matrix, target);
  return [
    [coeffs[0], coeffs[1], coeffs[2]],
    [coeffs[3], coeffs[4], coeffs[5]],
    [coeffs[6], coeffs[7], 1],
  ];
}

export function mapPoints(transform: number[][], points: [number, number][]): [number, number][] {
  return points.map(([x, y]) => {
    const w = transform[2][0] * x + transform[2][1] * y + transform[2][2];
    return [
      (transform[0][0] * x + transform[0][1] * y + transform[0][2]) / w,
      (transform[1][0] * x + transform[1][1] * y + transform[1][2]) / w,
    ];
  });
}

function patchMean(image: RgbImage, x: number, y: number, radius: number): [number, number, number] {
  const patch = image.patch(x, y, radius);
  if (patch.length === 0) throw new DecodeError("采样点落在图像外");
  let r = 0;
  let g = 0;
  let b = 0;
  const count = patch.length / 3;
  for (let i = 0; i < patch.length; i += 3) {
    r += patch[i];
    g += patch[i + 1];
    b += patch[i + 2];
  }
  return [r / count, g / count, b / count];
}

export function ringIsMixed(image: RgbImage, hit: FinderHit): boolean {
  const radius = hit.width / 4;
  let r = 0;
  let g = 0;
  let b = 0;
  for (let step = 0; step < 8; step += 1) {
    const angle = (step * Math.PI) / 4;
    const sample = patchMean(image, hit.x + radius * Math.cos(angle), hit.y + radius * Math.sin(angle), 1);
    r += sample[0];
    g += sample[1];
    b += sample[2];
  }
  r /= 8;
  g /= 8;
  b /= 8;
  return r > 90 && g > 90 && b < 100 && Math.abs(r - g) < 50;
}

export class FrameLocator {
  constructor(readonly geometry: { designCorners: () => [number, number][] }) {}

  locate(image: RgbImage): { transform: number[][]; corners: FinderHit[] } {
    const corners = orderCorners(findFinders(image));
    if (corners.some((hit) => ringIsMixed(image, hit))) throw new MixedFrame("定位图案红绿混叠，丢弃该帧");
    return {
      transform: homography(
        this.geometry.designCorners(),
        corners.map((hit) => [hit.x, hit.y]),
      ),
      corners,
    };
  }
}
