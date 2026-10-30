class GaloisField {
  readonly exp = new Uint16Array(512);
  readonly log = new Uint8Array(256);

  constructor() {
    let value = 1;
    for (let power = 0; power < 255; power += 1) {
      this.exp[power] = value;
      this.log[value] = power;
      value <<= 1;
      if (value & 0x100) value ^= 0x11d;
    }
    for (let power = 255; power < 512; power += 1) this.exp[power] = this.exp[power - 255];
  }

  mul(left: number, right: number): number {
    if (left === 0 || right === 0) return 0;
    return this.exp[this.log[left] + this.log[right]];
  }

  inv(value: number): number {
    if (value === 0) throw new Error("除零");
    return this.exp[255 - this.log[value]];
  }
}

const GF = new GaloisField();

function generator(nsym: number): number[] {
  let poly = [1];
  for (let power = 0; power < nsym; power += 1) {
    const product = new Array<number>(poly.length + 1).fill(0);
    poly.forEach((coef, index) => {
      product[index] ^= coef;
      product[index + 1] ^= GF.mul(coef, GF.exp[power]);
    });
    poly = product;
  }
  return poly;
}

function syndromes(codeword: number[], nsym: number): number[] {
  const out: number[] = [];
  for (let power = 0; power < nsym; power += 1) {
    let acc = 0;
    const root = GF.exp[power];
    for (const coef of codeword) acc = GF.mul(acc, root) ^ coef;
    out.push(acc);
  }
  return out;
}

function berlekampMassey(synd: number[]): number[] {
  let locator = [1];
  let previous = [1];
  let length = 0;
  let shift = 1;
  let last = 1;
  synd.forEach((syndrome, n) => {
    let delta = syndrome;
    for (let i = 1; i <= length; i += 1) delta ^= GF.mul(locator[i] ?? 0, synd[n - i]);
    if (delta === 0) {
      shift += 1;
      return;
    }
    const scale = GF.mul(delta, GF.inv(last));
    const term = new Array<number>(shift).fill(0).concat(previous);
    if (locator.length < term.length) locator = locator.concat(new Array(term.length - locator.length).fill(0));
    const updated = locator.slice();
    term.forEach((coef, i) => {
      updated[i] ^= GF.mul(scale, coef);
    });
    if (2 * length <= n) {
      previous = locator;
      locator = updated;
      length = n + 1 - length;
      last = delta;
      shift = 1;
    } else {
      locator = updated;
      shift += 1;
    }
  });
  while (locator.length > 1 && locator[locator.length - 1] === 0) locator.pop();
  return locator;
}

function evalLow(poly: number[], x: number): number {
  let acc = 0;
  let power = 1;
  for (const coef of poly) {
    acc ^= GF.mul(coef, power);
    power = GF.mul(power, x);
  }
  return acc;
}

function errorPositions(locator: number[], length: number): number[] {
  const positions: number[] = [];
  for (let pos = 0; pos < length; pos += 1) {
    const exponent = (255 - (length - 1 - pos)) % 255;
    if (evalLow(locator, GF.exp[exponent]) === 0) positions.push(pos);
  }
  return positions;
}

function solve(matrix: number[][], values: number[]): number[] {
  const size = values.length;
  const rows = matrix.map((row, i) => row.concat(values[i]));
  for (let col = 0; col < size; col += 1) {
    let pivot = -1;
    for (let row = col; row < size; row += 1) {
      if (rows[row][col] !== 0) {
        pivot = row;
        break;
      }
    }
    if (pivot < 0) throw new Error("RS 错误幅度方程组奇异");
    [rows[col], rows[pivot]] = [rows[pivot], rows[col]];
    const inverse = GF.inv(rows[col][col]);
    for (let index = col; index < size + 1; index += 1) rows[col][index] = GF.mul(rows[col][index], inverse);
    for (let row = 0; row < size; row += 1) {
      if (row === col || rows[row][col] === 0) continue;
      const factor = rows[row][col];
      for (let index = col; index < size + 1; index += 1) rows[row][index] ^= GF.mul(factor, rows[col][index]);
    }
  }
  return rows.map((row) => row[size]);
}

function magnitudes(synd: number[], positions: number[], length: number): number[] {
  const xs = positions.map((pos) => GF.exp[(length - 1 - pos) % 255]);
  const matrix = xs.map(() => [] as number[]);
  for (let power = 0; power < positions.length; power += 1) {
    xs.forEach((x, column) => {
      let value = 1;
      for (let i = 0; i < power; i += 1) value = GF.mul(value, x);
      matrix[power][column] = value;
    });
  }
  return solve(matrix, synd.slice(0, positions.length));
}

export class ReedSolomon {
  constructor(readonly parityBytes: number) {
    if (parityBytes <= 0) throw new Error("校验字节数必须为正");
  }

  encode(data: Uint8Array): Uint8Array {
    const nsym = this.parityBytes;
    if (data.length + nsym > 255) throw new Error("RS 码字最长 255 字节");
    const gen = generator(nsym);
    const message = Array.from(data).concat(new Array(nsym).fill(0));
    for (let index = 0; index < data.length; index += 1) {
      const coef = message[index];
      if (coef === 0) continue;
      for (let offset = 1; offset < gen.length; offset += 1) {
        message[index + offset] ^= GF.mul(gen[offset], coef);
      }
    }
    const out = new Uint8Array(data.length + nsym);
    out.set(data);
    for (let i = 0; i < nsym; i += 1) out[data.length + i] = message[message.length - nsym + i];
    return out;
  }

  decode(codeword: Uint8Array): Uint8Array {
    const nsym = this.parityBytes;
    const message = Array.from(codeword);
    const synd = syndromes(message, nsym);
    if (synd.every((value) => value === 0)) return codeword.slice(0, codeword.length - nsym);
    const locator = berlekampMassey(synd);
    const degree = locator.length - 1;
    if (degree <= 0 || degree > nsym / 2) throw new Error("RS 错误个数超出校验能力");
    const positions = errorPositions(locator, message.length);
    if (positions.length !== degree) throw new Error("RS 错误位置找不到");
    magnitudes(synd, positions, message.length).forEach((magnitude, i) => {
      message[positions[i]] ^= magnitude;
    });
    if (syndromes(message, nsym).some((value) => value !== 0)) throw new Error("RS 纠错后校验子不为零");
    return Uint8Array.from(message.slice(0, message.length - nsym));
  }
}
