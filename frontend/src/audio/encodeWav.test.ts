import { describe, it, expect, vi, afterEach } from "vitest";
import { blobToWav16k, float32ToWav } from "./encodeWav";

// jsdom's Blob has no arrayBuffer(); read via FileReader.
function bytes(blob: Blob): Promise<DataView> {
  return new Promise((resolve, reject) => {
    const r = new FileReader();
    r.onload = () => resolve(new DataView(r.result as ArrayBuffer));
    r.onerror = () => reject(r.error);
    r.readAsArrayBuffer(blob);
  });
}

describe("float32ToWav", () => {
  it("writes a 44-byte RIFF/WAVE PCM16 mono header", async () => {
    const wav = await bytes(float32ToWav(new Float32Array(3), 16000));
    const tag = (o: number) => String.fromCharCode(...[0, 1, 2, 3].map((i) => wav.getUint8(o + i)));
    expect([tag(0), tag(8), tag(12), tag(36)]).toEqual(["RIFF", "WAVE", "fmt ", "data"]);
    expect(wav.getUint32(4, true)).toBe(36 + 6);
    expect(wav.getUint16(20, true)).toBe(1);
    expect(wav.getUint16(22, true)).toBe(1);
    expect(wav.getUint32(24, true)).toBe(16000);
    expect(wav.getUint32(28, true)).toBe(32000);
    expect(wav.getUint16(34, true)).toBe(16);
    expect(wav.getUint32(40, true)).toBe(6);
  });

  it("has 44 + 2 bytes per sample and audio/wav type", () => {
    const blob = float32ToWav(new Float32Array(10), 16000);
    expect(blob.size).toBe(64);
    expect(blob.type).toBe("audio/wav");
  });

  it("clips out-of-range samples to the int16 range", async () => {
    const wav = await bytes(float32ToWav(new Float32Array([2, -2, 1, -1, 0.5]), 16000));
    const s = (i: number) => wav.getInt16(44 + i * 2, true);
    expect([s(0), s(1), s(2), s(3)]).toEqual([32767, -32768, 32767, -32768]);
    expect(s(4)).toBe(Math.trunc(0.5 * 0x7fff));
  });
});

describe("blobToWav16k", () => {
  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it("throws a friendly error and logs a diagnostic when decoding fails", async () => {
    class FakeAudioContext {
      decodeAudioData() {
        return Promise.reject(new DOMException("Unable to decode audio data", "EncodingError"));
      }
      close() {
        return Promise.resolve();
      }
    }
    vi.stubGlobal("AudioContext", FakeAudioContext);
    const warnSpy = vi.spyOn(console, "warn").mockImplementation(() => {});

    const blob = new Blob(["x"], { type: "audio/webm" });
    await expect(blobToWav16k(blob)).rejects.toThrow(
      "Couldn't process that recording — try again, holding a beat longer.",
    );
    expect(warnSpy).toHaveBeenCalledTimes(1);
    expect(warnSpy).toHaveBeenCalledWith("blobToWav16k decode failed", {
      size: blob.size,
      type: blob.type,
    });

    warnSpy.mockRestore();
  });
});
