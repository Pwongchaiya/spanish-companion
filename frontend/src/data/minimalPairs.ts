// Static minimal-pair word list for the listening-discrimination drill
// (roadmap item B6). Kept in sync by hand with the backend's copy
// (api/data/minimal_pairs.py) -- duplicated rather than fetched from a new
// endpoint, since it's static data the client needs at render time
// regardless (see that file's docstring for the reasoning).
export interface MinimalPair {
  a: string;
  b: string;
}

export const MINIMAL_PAIRS: MinimalPair[] = [
  { a: "pero", b: "perro" },
  { a: "caro", b: "carro" },
  { a: "pera", b: "perra" },
  { a: "coro", b: "corro" },
  { a: "cero", b: "cerro" },
  { a: "para", b: "parra" },
  { a: "foro", b: "forro" },
  { a: "moro", b: "morro" },
  { a: "papa", b: "papá" },
  { a: "como", b: "cómo" },
  { a: "hablo", b: "habló" },
  { a: "paso", b: "pasó" },
];

export function pickRandomPair(pairs: MinimalPair[] = MINIMAL_PAIRS): MinimalPair {
  return pairs[Math.floor(Math.random() * pairs.length)];
}

export function pickRandomWord(pair: MinimalPair): string {
  return Math.random() < 0.5 ? pair.a : pair.b;
}
