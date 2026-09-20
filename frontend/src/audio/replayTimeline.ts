// E3 replay timeline math, kept pure so it's testable without an <audio> element.

/** Marker left-offset as a percentage of the track, clamped to 0..100. */
export function markerPercent(offsetSeconds: number, durationSeconds: number): number {
  if (!(durationSeconds > 0)) return 0;
  return Math.min(100, Math.max(0, (offsetSeconds / durationSeconds) * 100));
}

/** Where to seek when a marker is clicked: a short lead-in before the flagged
 *  moment so the mistake is heard in context, never before 0 or past the end. */
export const SEEK_LEAD_IN_SECONDS = 2;

export function seekTarget(offsetSeconds: number, durationSeconds: number): number {
  return Math.min(Math.max(0, offsetSeconds - SEEK_LEAD_IN_SECONDS), Math.max(0, durationSeconds));
}

/** m:ss label for a marker's tooltip. */
export function formatOffset(seconds: number): string {
  const whole = Math.max(0, Math.floor(seconds));
  return `${Math.floor(whole / 60)}:${String(whole % 60).padStart(2, "0")}`;
}
