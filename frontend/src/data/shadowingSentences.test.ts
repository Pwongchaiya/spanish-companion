import { describe, it, expect } from "vitest";
import { SHADOWING_SENTENCES, pickRandomSentence } from "./shadowingSentences";

describe("shadowingSentences", () => {
  it("has ~15 unique sentences, all under 200 chars", () => {
    expect(SHADOWING_SENTENCES.length).toBeGreaterThanOrEqual(15);
    expect(new Set(SHADOWING_SENTENCES.map((s) => s.es)).size).toBe(SHADOWING_SENTENCES.length);
    SHADOWING_SENTENCES.forEach((s) => { expect(s.es.length).toBeLessThan(200); expect(s.en.length).toBeGreaterThan(0); });
  });

  it("pickRandomSentence never returns the excluded sentence", () => {
    const exclude = SHADOWING_SENTENCES[0].es;
    for (let i = 0; i < 200; i++) expect(pickRandomSentence(exclude).es).not.toBe(exclude);
  });

  it("pickRandomSentence returns a known sentence with no exclude", () => {
    expect(SHADOWING_SENTENCES).toContain(pickRandomSentence());
  });
});
