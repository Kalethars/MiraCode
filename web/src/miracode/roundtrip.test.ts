import { describe, expect, it } from "vitest";
import { MiraCode } from "./pipeline";
import { readAvi, writeAvi } from "./video";

describe("browser pipeline", () => {
  it("roundtrips text through an uncompressed avi", () => {
    const text = "MiraCode";
    const code = new MiraCode(16);
    const frames = code.encode(new TextEncoder().encode(text));
    const restored = new TextDecoder().decode(code.decode(readAvi(writeAvi(frames))));
    expect(restored).toBe(text);
  }, 30000);
});
