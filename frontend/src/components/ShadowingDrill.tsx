import { useEffect, useState } from "react";
import { apiClient } from "../api/client";
import type { PronunciationResult, WordScore } from "../api/types";
import { blobToWav16k } from "../audio/encodeWav";
import { pickRandomSentence } from "../data/shadowingSentences";
import { MAX_RECORD_MS, useRecorder } from "../hooks/useRecorder";
import { band } from "./PronunciationHeatmap";
import "./ShadowingDrill.css";

type DrillPhase = "recording" | "assessing" | "improved" | "weak" | "error";
type Drill = {
  word: string;
  before: number;
  after: number | null;
  detail: string | null;
  attempts: number;
  phase: DrillPhase;
};
type Scored = WordScore & { accuracy: number };

const PASS = 80;
const R = 54;
const CIRC = 2 * Math.PI * R;
const clock = (ms: number) => `${Math.floor(ms / 60000)}:${String(Math.floor(ms / 1000) % 60).padStart(2, "0")}`;
const MAX_CLOCK = clock(MAX_RECORD_MS);
const errText = (err: unknown, fallback: string) => (err instanceof Error ? err.message : fallback);
const pct = (v: number) => `${Math.min(Math.max(v, 0), 100)}%`;

// ponytail: local useState only, same call as MinimalPairDrill -- not wired
// into the toast/backoff machinery; a failed attempt is one retry click away.
// One file: column state derives from recorder/submitting/error/result; the
// five word-drill states are sub-states of "results" (only the aside swaps).
export function ShadowingDrill() {
  const [sentence, setSentence] = useState(() => pickRandomSentence());
  const [audioUrl, setAudioUrl] = useState<string | null>(null);
  const [playing, setPlaying] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<PronunciationResult | null>(null);
  const [attempt, setAttempt] = useState(0);
  const [drill, setDrill] = useState<Drill | null>(null);
  const [status, setStatus] = useState("");
  const [elapsed, setElapsed] = useState(0);
  const [handled, setHandled] = useState<Blob | null>(null);
  const recorder = useRecorder();
  const recording = recorder.status === "recording";

  useEffect(() => {
    if (!recording) return;
    const t0 = Date.now();
    setElapsed(0);
    const id = setInterval(() => setElapsed(Date.now() - t0), 250);
    return () => clearInterval(id);
  }, [recording]);

  // A finished take is scored once: as a word drill if one is recording, else as the sentence.
  useEffect(() => {
    const blob = recorder.blob;
    if (recorder.status !== "done" || !blob || blob === handled) return;
    setHandled(blob);
    if (drill?.phase === "recording") void scoreDrill(blob, drill);
    else if (!result && !submitting) void submit(blob);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [recorder.status, recorder.blob]);

  function next() {
    setSentence(pickRandomSentence(sentence.es));
    setAudioUrl(null);
    setError(null);
    setResult(null);
    setDrill(null);
    setAttempt(0);
    setStatus("");
  }

  async function play(text: string, rate = 1) {
    setPlaying(true);
    setError(null);
    try {
      const blob = rate === 1 ? await apiClient.synthesizeSpeech(text) : await apiClient.synthesizeSpeech(text, rate);
      setAudioUrl(URL.createObjectURL(blob));
    } catch {
      const msg = "Couldn't load the reference audio. Try again.";
      setError(msg);
      setStatus(msg);
    } finally {
      setPlaying(false);
    }
  }

  async function submit(blob: Blob | null = recorder.blob) {
    if (!blob) return;
    setSubmitting(true);
    setError(null);
    try {
      const wav = await blobToWav16k(blob);
      setResult(await apiClient.assessPronunciation(wav, sentence.es, false));
      setAttempt((n) => n + 1);
    } catch (err) {
      // json<T> puts the server's {"error"} text (400/413/500) on err.message.
      setError(errText(err, "Couldn't score that attempt. Try again."));
    } finally {
      setSubmitting(false);
    }
  }

  function recordSentence() {
    setResult(null);
    setDrill(null);
    setStatus("");
    void recorder.start();
  }

  function startDrill(word: string, before: number) {
    setDrill((d) => ({
      word,
      before,
      after: null,
      detail: null,
      attempts: d?.word === word ? d.attempts : 0,
      phase: "recording",
    }));
    setStatus(`Recording the word ${word}.`);
    void recorder.start();
  }

  function leaveDrill() {
    if (recording) recorder.stop(); // result is set, so that take is discarded unscored
    setDrill(null);
    setStatus("");
  }

  async function scoreDrill(blob: Blob, d: Drill) {
    setDrill({ ...d, phase: "assessing" });
    setStatus(`Scoring ${d.word}.`);
    let done: Drill;
    try {
      const wav = await blobToWav16k(blob);
      // Score is words[0].accuracy, never overall: enable_miscue scores extra speech as
      // insertions against a one-word reference, and fluency over one word is noise.
      const res = await apiClient.assessPronunciation(wav, d.word, true);
      const after = res.words[0]?.accuracy ?? null;
      const attempts = d.attempts + 1;
      done =
        after === null
          ? { ...d, attempts, phase: "error", detail: "No score returned for that word." }
          : { ...d, attempts, after, phase: after >= PASS ? "improved" : "weak" };
    } catch (err) {
      done = { ...d, phase: "error", detail: errText(err, "Couldn't score that clip.") };
    }
    setDrill(done);
    setStatus(
      done.phase === "improved"
        ? `${d.word} scored ${Math.round(done.after ?? 0)}, up from ${Math.round(d.before)}.`
        : done.phase === "weak"
          ? `${d.word} scored ${Math.round(done.after ?? 0)}, still under the bar.`
          : "Couldn't score that clip. Record the word again.",
    );
  }

  const shownError = error ?? recorder.error;
  const words: WordScore[] = result?.words ?? [];
  const scored = words.filter((w): w is Scored => w.accuracy !== null);
  const weak = scored.filter((w) => w.accuracy < PASS);
  const lowest = scored.reduce<Scored | null>((m, w) => (m === null || w.accuracy < m.accuracy ? w : m), null);
  const highest = scored.reduce((m, w) => Math.max(m, w.accuracy), 0);
  const drillPhase: DrillPhase | null = drill
    ? drill.phase === "recording" && recorder.error
      ? "error"
      : drill.phase
    : null;

  const col =
    recording && !drill
      ? "recording"
      : submitting
        ? "loading"
        : shownError && !result
          ? "error"
          : result
            ? "results"
            : "pre";
  const timer = `${clock(elapsed)} / ${MAX_CLOCK}`;
  const en = (
    <p className="en" lang="en">
      {sentence.en}
    </p>
  );

  return (
    <div className="view sd">
      <div className="wrap">
        <div className="col">
          {col === "pre" && (
            <section className="stage" aria-label="Ready to record">
              <p className="kicker">Listen, then repeat the sentence</p>
              <p className="lead">{sentence.es}</p>
              {en}
              <div className="row">
                <button className="ghost" type="button" onClick={() => play(sentence.es)} disabled={playing || recording}>
                  {playing ? "Loading…" : "▶ Play"}
                </button>
                <button className="primary" type="button" onClick={recordSentence}>
                  ● Record
                </button>
              </div>
              <p className="kicker quiet">Max {MAX_CLOCK}</p>
            </section>
          )}

          {col === "recording" && (
            <section className="stage" aria-label="Recording">
              <div className="rec-ring" aria-hidden="true">
                <i />
              </div>
              <p className="kicker ember">Recording</p>
              <p className="rec-time">{timer}</p>
              <p className="lead small">{sentence.es}</p>
              <button className="stop-btn" type="button" onClick={recorder.stop}>
                <i aria-hidden="true" /> Stop &amp; score
              </button>
            </section>
          )}

          {col === "loading" && (
            <section className="stage" aria-label="Assessing" aria-busy="true">
              <Spinner size={28} />
              <p className="kicker">Assessing · Azure es-ES</p>
              <div className="sk-rows" aria-hidden="true">
                <div className="sk" />
                <div className="sk" />
                <div className="sk" />
              </div>
            </section>
          )}

          {col === "error" && (
            <section className="stage" aria-label="Assessment failed">
              <div className="err">
                <span className="lbl">Assessment failed</span>
                <p>Couldn’t score that attempt.{recorder.blob ? " Your recording is still here — try again." : ""}</p>
                <span className="detail">{shownError}</span>
              </div>
              <div className="row">
                {recorder.blob && (
                  <button className="primary" type="button" onClick={() => submit()}>
                    Try again
                  </button>
                )}
                <button className="ghost" type="button" onClick={recordSentence}>
                  ● Record again
                </button>
              </div>
            </section>
          )}

          {col === "results" && result && (
            <>
              <section className="hero">
                <div className={`dial ${band(result.overall) === "good" ? "" : band(result.overall)}`}>
                  <svg
                    width="128"
                    height="128"
                    viewBox="0 0 128 128"
                    role="img"
                    aria-label={`Overall ${Math.round(result.overall)} out of 100`}
                  >
                    <circle className="track" cx="64" cy="64" r={R} fill="none" strokeWidth="1.5" />
                    <circle
                      className="fill"
                      cx="64"
                      cy="64"
                      r={R}
                      fill="none"
                      strokeWidth="4"
                      style={{ strokeDasharray: `${(CIRC * Math.min(Math.max(result.overall, 0), 100)) / 100} ${CIRC}` }}
                    />
                  </svg>
                  <div className="num">{Math.round(result.overall)}</div>
                </div>
                <p className="kicker">Overall · attempt {attempt}</p>
                <p className="verdict">
                  {weak.length === 0 ? (
                    <>
                      Clean the whole way through. <em>Nothing to fix here.</em>
                    </>
                  ) : (
                    <>
                      Solid rhythm.{" "}
                      <em>
                        {weak.length === 1 ? "One word is holding this back." : `${weak.length} words are holding this back.`}
                      </em>
                    </>
                  )}
                </p>
                <p className="sentence">{sentence.es}</p>
                {en}
              </section>

              <section className="meters" aria-label="Score breakdown">
                {(
                  [
                    ["Accuracy", result.accuracy],
                    ["Fluency", result.fluency],
                    ["Completeness", result.completeness],
                  ] as const
                ).map(([label, v]) => (
                  <div className="meter" key={label}>
                    <span className="m-label">{label}</span>
                    <span className="m-val">{Math.round(v)}</span>
                    <span className="m-bar">
                      <i style={{ width: pct(v) }} />
                    </span>
                  </div>
                ))}
              </section>

              <section aria-label="Word scores">
                <div className="hd">
                  <span className="kicker">Per word</span>
                  <span className="kicker quiet">tap to replay</span>
                </div>
                <div className="cells">
                  {words.map((w, i) => {
                    const n = w.accuracy === null ? "–" : Math.round(w.accuracy);
                    const said = w.accuracy === null ? "no score" : `scored ${n}`;
                    return (
                      <button
                        key={i}
                        type="button"
                        className={`cell ${band(w.accuracy)}`}
                        aria-label={`${w.word}, ${said}${w.error_type !== "None" ? `, ${w.error_type}` : ""}. Replay.`}
                        onClick={() => play(w.word)}
                      >
                        <span className="w">{w.word}</span>
                        <span className="n">{n}</span>
                      </button>
                    );
                  })}
                </div>
                <p className="foot">word-level only · es-ES returns no phoneme breakdown</p>
              </section>
            </>
          )}

          <p className="status" role="status" aria-live="polite">
            {status}
          </p>

          {col === "results" ? (
            <div className="tail">
              <button className="primary" type="button" onClick={recordSentence}>
                ● Record again
              </button>
              <button className="linkish" type="button" onClick={next}>
                Next sentence →
              </button>
            </div>
          ) : (
            <button className="linkish next" type="button" onClick={next}>
              Next sentence →
            </button>
          )}
          {audioUrl && <audio src={audioUrl} autoPlay data-testid="shadow-audio" />}
        </div>

        {drill && drillPhase ? (
          <details className="coach drill" open data-result={drillPhase === "improved" ? "up" : ""}>
            <summary>
              Drill{" "}
              <span className="sum-extra">
                {drill.word} · {drillTag(drillPhase, drill.after)}
              </span>
            </summary>
            <div className="word">{drill.word}</div>

            {drillPhase === "recording" && (
              <div>
                <div className="drill-live">
                  <span className="dot" aria-hidden="true" />
                  <span className="rec-time">{timer}</span>
                  <span className="lbl">Rec</span>
                </div>
                <p className="why">Just the word, once. Nothing before or after it.</p>
                <div className="act-row">
                  <button className="stop-btn wide" type="button" onClick={recorder.stop}>
                    <i aria-hidden="true" /> Stop &amp; score
                  </button>
                  <button className="linkish wide" type="button" onClick={leaveDrill}>
                    Cancel
                  </button>
                </div>
              </div>
            )}

            {drillPhase === "assessing" && (
              <div aria-busy="true">
                <div className="drill-spin">
                  <Spinner size={18} />
                  <span className="kicker">Scoring one word</span>
                </div>
                <div className="sk-aside" aria-hidden="true">
                  <div className="sk" />
                  <div className="sk" />
                  <div className="sk short" />
                </div>
              </div>
            )}

            {(drillPhase === "improved" || drillPhase === "weak") && (
              <div>
                <dl className="rows">
                  <dt>Word score</dt>
                  <dd className={drillPhase === "improved" ? "up" : "bad"}>
                    <span className="was">{Math.round(drill.before)}</span>
                    {Math.round(drill.after ?? 0)} / 100
                  </dd>
                  <dt>Attempts</dt>
                  <dd>{drill.attempts}</dd>
                </dl>
                <p className="why">
                  {drillPhase === "improved"
                    ? "Better. Put it back in the sentence while it’s fresh."
                    : "Still short. Hear it at 0.6× once, then copy the ending exactly."}
                </p>
                <div className="act-row">
                  {drillPhase === "improved" ? (
                    <>
                      <button className="ghost" type="button" onClick={() => startDrill(drill.word, drill.before)}>
                        ● Again
                      </button>
                      <button className="ghost" type="button" onClick={() => play(drill.word)}>
                        ▶ Hear
                      </button>
                      <button className="primary wide" type="button" onClick={recordSentence}>
                        ↺ Whole sentence
                      </button>
                    </>
                  ) : (
                    <>
                      <button className="ghost wide" type="button" onClick={() => play(drill.word, 0.6)}>
                        ◐ Hear at 0.6×
                      </button>
                      <button className="ghost wide" type="button" onClick={() => startDrill(drill.word, drill.before)}>
                        ● Record again
                      </button>
                      <button className="linkish wide" type="button" onClick={leaveDrill}>
                        Back to the sentence
                      </button>
                    </>
                  )}
                </div>
              </div>
            )}

            {drillPhase === "error" && (
              <div>
                <div className="err">
                  <span className="lbl">Couldn’t score that</span>
                  <p>Couldn’t score that clip. Record the word again, a touch louder.</p>
                  <span className="detail">{drill.detail ?? recorder.error}</span>
                </div>
                <div className="act-row">
                  <button className="ghost wide" type="button" onClick={() => startDrill(drill.word, drill.before)}>
                    ● Record again
                  </button>
                  <button className="linkish wide" type="button" onClick={leaveDrill}>
                    Back to the sentence
                  </button>
                </div>
              </div>
            )}
          </details>
        ) : col === "results" && lowest && weak.length > 0 ? (
          <details className="coach" open>
            <summary>
              Fix{" "}
              <span className="sum-extra">
                {lowest.word} · {Math.round(lowest.accuracy)}
              </span>
            </summary>
            <div className="word">{lowest.word}</div>
            <dl className="rows">
              <dt>Score</dt>
              <dd className="bad">{Math.round(lowest.accuracy)} / 100</dd>
              <dt>Azure</dt>
              <dd className="bad">{lowest.error_type === "None" ? "Below the bar" : lowest.error_type}</dd>
              <dt>Rank</dt>
              <dd>
                {scored.filter((w) => w.accuracy > lowest.accuracy).length + 1} of {scored.length}
              </dd>
            </dl>
            <div className="act-row">
              <button className="ghost" type="button" onClick={() => play(lowest.word)} disabled={playing}>
                ▶ Hear
              </button>
              <button className="ghost" type="button" onClick={() => play(lowest.word, 0.6)} disabled={playing}>
                ◐ 0.6×
              </button>
              <button className="ghost wide" type="button" onClick={() => startDrill(lowest.word, lowest.accuracy)}>
                ● Record just this word
              </button>
            </div>
            <p className="aside-foot">
              <button className="linkish" type="button" onClick={() => play(sentence.es)}>
                ▶ Whole-sentence reference
              </button>
            </p>
          </details>
        ) : col === "results" ? (
          <details className="coach calm" open>
            <summary>
              Clear <span className="sum-extra">no weak words</span>
            </summary>
            <div className="word">Nothing to fix.</div>
            <dl className="rows">
              <dt>Weak words</dt>
              <dd>0 of {scored.length}</dd>
              <dt>Lowest</dt>
              <dd>{lowest ? `${lowest.word} · ${Math.round(lowest.accuracy)}` : "–"}</dd>
              <dt>Range</dt>
              <dd>{lowest ? `${Math.round(lowest.accuracy)} – ${Math.round(highest)}` : "–"}</dd>
            </dl>
            <div className="act-row">
              <button className="ghost wide" type="button" onClick={() => play(sentence.es)} disabled={playing}>
                ▶ Hear the reference
              </button>
            </div>
          </details>
        ) : col === "error" ? null : (
          <details className="coach placeholder" open aria-busy={col === "loading"}>
            <summary>Coach</summary>
            {col === "loading" ? (
              <div className="sk-aside" aria-hidden="true">
                <div className="sk tall" />
                <div className="sk" />
                <div className="sk" />
                <div className="sk short" />
              </div>
            ) : (
              <p className="coach-note">
                {col === "recording"
                  ? "Listening. Say it once, at your own pace."
                  : "After scoring, this ledger lists the weakest word, its score, and what Azure called it."}
              </p>
            )}
          </details>
        )}
      </div>
    </div>
  );
}

function drillTag(phase: DrillPhase, after: number | null): string {
  if (phase === "recording") return "recording";
  if (phase === "assessing") return "scoring";
  if (phase === "error") return "failed";
  return String(Math.round(after ?? 0));
}

function Spinner({ size }: { size: number }) {
  return (
    <svg className="spin" width={size} height={size} viewBox="0 0 34 34" fill="none" aria-hidden="true">
      <circle cx="17" cy="17" r="14" stroke="var(--border)" strokeWidth="2.5" />
      <path d="M31 17A14 14 0 0 0 17 3" stroke="var(--accent)" strokeWidth="2.5" strokeLinecap="round" />
    </svg>
  );
}
