// Static sentences for the pronunciation shadowing drill. Each < 200 chars
// (the backend's reference-text limit); chosen to cover rr/r, j, ñ, ll, b/v,
// diphthongs and stress contrasts.
export const SHADOWING_SENTENCES: string[] = [
  "El perro de Rosa corre rápido por el carril.",
  "Pedro pidió pera y el perro pidió carne.",
  "Rafael reparte ramos de rosas rojas.",
  "El jefe dejó el equipaje en la caja.",
  "Juan juega con el juguete de Julia.",
  "La niña del pueblo compra piñas en España.",
  "El año pasado mi hermano se fue a la montaña.",
  "La lluvia llegó a la calle y llenó la olla.",
  "Ella llama a la gallina amarilla.",
  "Voy a beber un vaso de vino en la ventana.",
  "El barco viejo bajó por el río con la brisa.",
  "Los aeropuertos están cerca de la ciudad, pero no del puerto.",
  "Cuando puedo, escucho el cuento del ciego con paciencia.",
  "Mañana hablaré con el médico sobre el número que me dio.",
  "La cámara está en la cárcel, no en el cáncer ni en la cama.",
];

export function pickRandomSentence(exclude?: string): string {
  const pool = SHADOWING_SENTENCES.filter((s) => s !== exclude);
  return pool[Math.floor(Math.random() * pool.length)];
}
