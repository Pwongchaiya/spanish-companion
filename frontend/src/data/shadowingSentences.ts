// Static sentences for the pronunciation shadowing drill. Each `es` < 200 chars
// (the backend's reference-text limit); chosen to cover rr/r, j, ñ, ll, b/v,
// diphthongs and stress contrasts. `en` is display-only -- TTS speaks `es`.
export type ShadowingSentence = { es: string; en: string };

export const SHADOWING_SENTENCES: ShadowingSentence[] = [
  { es: "El perro de Rosa corre rápido por el carril.", en: "Rosa's dog runs fast along the lane." },
  { es: "Pedro pidió pera y el perro pidió carne.", en: "Pedro asked for a pear and the dog asked for meat." },
  { es: "Rafael reparte ramos de rosas rojas.", en: "Rafael hands out bunches of red roses." },
  { es: "El jefe dejó el equipaje en la caja.", en: "The boss left the luggage in the box." },
  { es: "Juan juega con el juguete de Julia.", en: "Juan plays with Julia's toy." },
  { es: "La niña del pueblo compra piñas en España.", en: "The girl from the village buys pineapples in Spain." },
  { es: "El año pasado mi hermano se fue a la montaña.", en: "Last year my brother went off to the mountains." },
  { es: "La lluvia llegó a la calle y llenó la olla.", en: "The rain reached the street and filled the pot." },
  { es: "Ella llama a la gallina amarilla.", en: "She calls the yellow hen." },
  { es: "Voy a beber un vaso de vino en la ventana.", en: "I'm going to drink a glass of wine at the window." },
  { es: "El barco viejo bajó por el río con la brisa.", en: "The old boat went down the river with the breeze." },
  {
    es: "Los aeropuertos están cerca de la ciudad, pero no del puerto.",
    en: "The airports are near the city, but not near the port.",
  },
  { es: "Cuando puedo, escucho el cuento del ciego con paciencia.", en: "When I can, I listen to the blind man's story with patience." },
  {
    es: "Mañana hablaré con el médico sobre el número que me dio.",
    en: "Tomorrow I'll talk to the doctor about the number he gave me.",
  },
  { es: "Siempre hablo con Marta, pero ayer ella no habló conmigo.", en: "I always talk to Marta, but yesterday she didn't talk to me." },
];

export function pickRandomSentence(exclude?: string): ShadowingSentence {
  const pool = SHADOWING_SENTENCES.filter((s) => s.es !== exclude);
  return pool[Math.floor(Math.random() * pool.length)];
}
