const TARGET_RATE = 16000;

// PCM16 little-endian mono WAV: 44-byte RIFF/WAVE header + samples.
export function float32ToWav(samples: Float32Array, sampleRate: number): Blob {
  const buf = new ArrayBuffer(44 + samples.length * 2);
  const v = new DataView(buf);
  const str = (off: number, s: string) => [...s].forEach((c, i) => v.setUint8(off + i, c.charCodeAt(0)));
  str(0, "RIFF");
  v.setUint32(4, 36 + samples.length * 2, true);
  str(8, "WAVE");
  str(12, "fmt ");
  v.setUint32(16, 16, true); // fmt chunk size
  v.setUint16(20, 1, true); // PCM
  v.setUint16(22, 1, true); // mono
  v.setUint32(24, sampleRate, true);
  v.setUint32(28, sampleRate * 2, true); // byte rate
  v.setUint16(32, 2, true); // block align
  v.setUint16(34, 16, true); // bits per sample
  str(36, "data");
  v.setUint32(40, samples.length * 2, true);
  samples.forEach((s, i) => {
    const c = Math.max(-1, Math.min(1, s));
    v.setInt16(44 + i * 2, c < 0 ? c * 0x8000 : c * 0x7fff, true);
  });
  return new Blob([buf], { type: "audio/wav" });
}

// Decode any browser-recorded blob, resample to 16 kHz mono, encode WAV.
// Not unit-tested: jsdom has no AudioContext.
export async function blobToWav16k(blob: Blob): Promise<Blob> {
  const ctx = new AudioContext();
  try {
    const bytes = await blob.arrayBuffer();
    const decoded = await ctx.decodeAudioData(bytes);
    const length = Math.ceil(decoded.duration * TARGET_RATE);
    const offline = new OfflineAudioContext(1, length, TARGET_RATE);
    const src = offline.createBufferSource();
    src.buffer = decoded;
    src.connect(offline.destination); // downmixes to mono
    src.start();
    const rendered = await offline.startRendering();
    return float32ToWav(rendered.getChannelData(0), TARGET_RATE);
  } finally {
    void ctx.close();
  }
}
