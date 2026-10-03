"""RAG eval harness for the Review Mode flow: retrieve(corrected) -> explain(flag, chunks).

Runs evals/questions.yaml against the real pipeline (real Postgres/pgvector, real Gemini),
then writes evals/reports/<date>.json. Two layers, scored separately (rag-eval-skill.md):
  1. retrieval  -- hit rate @ k and MRR against each question's expected_topic
  2. answers    -- LLM judge grades each explanation against expected_answer

Usage:
  python evals/run_eval.py                          # full run, writes a report
  python evals/run_eval.py --retrieval-only         # no Gemini calls
  python evals/run_eval.py --baseline evals/reports/2026-09-25.json   # exit 1 on regression
  python evals/run_eval.py --self-test              # scoring logic only, no DB/network

Config (env / .env): DATABASE_URL, GEMINI_API_KEY, RETRIEVAL_TOP_K (3), RETRIEVAL_MAX_DISTANCE (0.59),
EXPLAIN_TOP_K (3, read by GenerationService itself -- #64), GENERATION_TEMPERATURE (0 -- #86: pins
the shared/draft broker so explain()'s draft stops varying run to run, same fix as api/app.py's
Review wiring), GROUNDING_JUDGE_TEMPERATURE (0 -- #68: pins GenerationService's reflective grounding
judge, same fix as api/app.py's Review wiring), GENERATION_RETRY_ATTEMPTS (5 -- #92: retries transient
503/429s on all three Gemini brokers), EVAL_JUDGE_MODEL (defaults to GEMINI_MODEL),
EVAL_JUDGE_TEMPERATURE (0 -- #68: pins this eval's own answer-quality judge only, so its sampling
noise doesn't get scored as a retrieval/generation regression), EVAL_REGRESSION_TOLERANCE (0.15 --
#68: measured 2026-10-02 on GENERATION_TEMPERATURE/GROUNDING_JUDGE_TEMPERATURE/EVAL_JUDGE_TEMPERATURE
all pinned to 0 -- answer_pass_rate over 5 runs: 0.2917, 0.2917, 0.3333, 0.4167, 0.3333, spread
(max-min) 0.125, rounded up to the next 0.05).
"""

import argparse
import json
import os
import sys
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from types import SimpleNamespace
from typing import Optional

import yaml

EVALS_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(EVALS_DIR.parent))

# Versioned with the question set. XML tags keep the explanation from being read as instructions.
JUDGE_PROMPT = """You grade a Spanish tutor's explanation of a learner's mistake.

<learner_said>{said}</learner_said>
<correction>{corrected}</correction>
<source_excerpt>{excerpt}</source_excerpt>
<explanation>{explanation}</explanation>
<expected_gist>{expected}</expected_gist>

PASS only if the explanation (a) conveys the expected gist and (b) claims nothing the source excerpt
does not support. Reply with exactly one line: "PASS: <reason>" or "FAIL: <reason>"."""

METRICS = ("hit_rate", "mrr", "answer_pass_rate")


@dataclass
class Result:
    id: str
    expected_topic: Optional[str]
    retrieved_topics: list
    rank: Optional[int]  # 1-based rank of first chunk with expected_topic; None = miss
    answer_pass: Optional[bool] = None
    answer_reason: str = ""
    error: str = ""


def score_retrieval(expected_topic: Optional[str], retrieved_topics: list) -> tuple[bool, Optional[int]]:
    """(hit, rank). A null expected_topic hits only when nothing is retrieved (Review then falls back)."""
    if expected_topic is None:
        return (not retrieved_topics, None)
    for i, topic in enumerate(retrieved_topics, start=1):
        if topic == expected_topic:
            return (True, i)
    return (False, None)


def summarize(results: list) -> dict:
    def block(rs: list) -> dict:
        hits = [score_retrieval(r.expected_topic, r.retrieved_topics)[0] for r in rs]
        ranked = [r for r in rs if r.expected_topic is not None]
        graded = [r.answer_pass for r in rs if r.answer_pass is not None]
        return {
            "n": len(rs),
            "hit_rate": sum(hits) / len(rs) if rs else 0.0,
            "mrr": sum(1 / r.rank for r in ranked if r.rank) / len(ranked) if ranked else 0.0,
            "answer_pass_rate": sum(graded) / len(graded) if graded else None,
        }

    by_topic: dict = {}
    for r in results:
        by_topic.setdefault(r.expected_topic or "null", []).append(r)
    return {"overall": block(results), "by_topic": {t: block(rs) for t, rs in sorted(by_topic.items())}}


def regressions(current: dict, baseline: dict, tolerance: float) -> list:
    out = []
    for m in METRICS:
        cur, base = current["overall"].get(m), baseline["overall"].get(m)
        if cur is not None and base is not None and cur < base - tolerance:
            out.append(f"{m}: {cur:.3f} < baseline {base:.3f}")
    return out


def build_pipeline():
    """Same classes and knobs as api/app.py's Review wiring -- the eval must hit the production path."""
    from dotenv import load_dotenv

    load_dotenv(EVALS_DIR.parent / ".env")
    from api.brokers.logging import StdlibLoggingBroker
    from rag.brokers.chunk_repository import SqlAlchemyChunkRepositoryBroker
    from rag.brokers.embedding_model import SentenceTransformerEmbeddingModelBroker
    from rag.brokers.generation import GeminiGenerationBroker
    from rag.services.foundations.chunk_repository import ChunkRepositoryService
    from rag.services.foundations.embedding_model import EmbeddingModelService
    from rag.services.foundations.generation import GenerationService
    from rag.services.orchestrations.retrieval import HybridRetrievalOrchestrationService
    from rag.services.orchestrations.retrieval.strategies.dense import DenseVectorStrategy
    from rag.services.orchestrations.retrieval.strategies.filters import MaxDistanceFilter
    from rag.services.orchestrations.retrieval.strategies.fusion import PassThroughRankFusion
    from rag.services.orchestrations.retrieval.strategies.lexical import LexicalStrategy

    # ponytail: third copy of this wiring (app.py, app_public.py); extract a shared builder if it drifts.
    log = StdlibLoggingBroker()
    chunks = ChunkRepositoryService(SqlAlchemyChunkRepositoryBroker(os.environ["DATABASE_URL"]), logging_broker=log)
    retrieval = HybridRetrievalOrchestrationService(
        EmbeddingModelService(SentenceTransformerEmbeddingModelBroker(), logging_broker=log),
        strategies=[DenseVectorStrategy(chunks, logging_broker=log)],
        fusion=PassThroughRankFusion(logging_broker=log),
        filters=[MaxDistanceFilter(float(os.getenv("RETRIEVAL_MAX_DISTANCE", "0.59")), logging_broker=log)],
        alternate_strategy=LexicalStrategy(chunks, logging_broker=log),
        candidate_pool=int(os.getenv("RETRIEVAL_CANDIDATE_POOL", "50")),
        logging_broker=log,
    )
    generation = GenerationService(
        # #86: same fix as api/app.py's Review wiring -- the shared/draft broker had
        # no temperature set, so explain()'s draft sampled at the API's default
        # (nonzero) temperature and varied run to run.
        # #92: same retry as api/app.py's Review wiring -- un-retried 503s were
        # scored as fallbacks and blamed on the grounding judge.
        GeminiGenerationBroker(
            temperature=float(os.getenv("GENERATION_TEMPERATURE", "0")),
            retry_attempts=int(os.getenv("GENERATION_RETRY_ATTEMPTS", "5")),
        ),
        logging_broker=log,
        # #68: same fix as api/app.py's Review wiring -- the reflective grounding
        # judge randomly rejected good drafts at the default (nonzero) temperature
        # it shared with the draft call itself.
        judge_broker=GeminiGenerationBroker(
            temperature=float(os.getenv("GROUNDING_JUDGE_TEMPERATURE", "0")),
            retry_attempts=int(os.getenv("GENERATION_RETRY_ATTEMPTS", "5")),
        ),
    )
    # #68: pin the eval's own answer-quality judge to temperature 0 -- draft/grounding
    # stay at the API default (unset), so only this judge's own noise is removed.
    judge = GeminiGenerationBroker(
        model_name=os.getenv("EVAL_JUDGE_MODEL") or None,
        temperature=float(os.getenv("EVAL_JUDGE_TEMPERATURE", "0")),
        retry_attempts=int(os.getenv("GENERATION_RETRY_ATTEMPTS", "5")),
    )
    return retrieval, generation, judge


def run(questions: list, retrieval_only: bool) -> list:
    retrieval, generation, judge = build_pipeline()
    top_k = int(os.getenv("RETRIEVAL_TOP_K", "3"))
    results = []
    for q in questions:
        r = Result(q["id"], q["expected_topic"], [], None)
        try:
            chunks = retrieval.retrieve(query=q["corrected"], top_k=top_k, category=q["category"])
            r.retrieved_topics = [c.topic for c in chunks]
            _, r.rank = score_retrieval(r.expected_topic, r.retrieved_topics)
            if not retrieval_only:
                r.answer_pass, r.answer_reason = grade(q, chunks, generation, judge)
        except Exception as e:  # one bad question must not sink the run; it's reported instead
            r.error = f"{type(e).__name__}: {e}"
        results.append(r)
        print(f"{r.id}: rank={r.rank} topics={r.retrieved_topics} answer={r.answer_pass} {r.error}")
    return results


def grade(q: dict, chunks: list, generation, judge) -> tuple[bool, str]:
    if not chunks:  # Review Mode's no-match path returns the fallback text
        return (q["expected_topic"] is None, "no chunks -> fallback")
    flag = SimpleNamespace(said=q["said"], corrected=q["corrected"], category=q["category"])
    # #64: pass the full retrieved list, same as Review -- GenerationService
    # grounds on its own EXPLAIN_TOP_K slice, not just chunks[0].
    exp = generation.explain(flag, chunks)
    if q["expected_topic"] is None:
        return (exp.is_fallback, "fallback" if exp.is_fallback else f"invented: {exp.explanation[:80]}")
    if exp.is_fallback:
        return (False, "fallback despite expected topic")
    verdict = judge.generate(
        JUDGE_PROMPT.format(
            said=q["said"],
            corrected=q["corrected"],
            # #68: the draft (GenerationService.explain(), #64) was built from and
            # grounded on the joined top EXPLAIN_TOP_K chunks, not just chunks[0] --
            # judging against exp.source_excerpt (chunks[0] alone) produced false
            # "not supported by the source excerpt" FAILs whenever the draft cited
            # chunks[1:]. Join the same slice the draft actually saw instead.
            excerpt="\n\n".join(c.content for c in chunks[: int(os.getenv("EXPLAIN_TOP_K", "3"))]),
            explanation=exp.explanation,
            expected=q["expected_answer"],
        )
    ).strip()
    return (verdict.upper().startswith("PASS"), verdict)


def self_test() -> None:
    assert score_retrieval("a", ["b", "a"]) == (True, 2)
    assert score_retrieval("a", ["b"]) == (False, None)
    assert score_retrieval(None, []) == (True, None)
    assert score_retrieval(None, ["a"]) == (False, None)
    rs = [
        Result("q1", "a", ["a"], 1, True),
        Result("q2", "a", ["b", "a"], 2, False),
        Result("q3", None, [], None, True),
        Result("q4", "b", ["c"], None, None),
    ]
    s = summarize(rs)["overall"]
    assert s["n"] == 4 and s["hit_rate"] == 0.75
    assert abs(s["mrr"] - (1 + 0.5) / 3) < 1e-9  # null-topic questions excluded from MRR
    assert abs(s["answer_pass_rate"] - 2 / 3) < 1e-9  # ungraded (None) excluded
    base = {"overall": {"hit_rate": 0.8, "mrr": 0.1, "answer_pass_rate": None}}
    assert regressions({"overall": s}, base, 0.0) == ["hit_rate: 0.750 < baseline 0.800"]
    assert regressions({"overall": s}, base, 0.1) == []
    print("self-test ok")


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--questions", default=str(EVALS_DIR / "questions.yaml"))
    p.add_argument("--retrieval-only", action="store_true")
    p.add_argument("--baseline", help="report JSON to compare against; exit 1 on regression")
    p.add_argument("--self-test", action="store_true")
    args = p.parse_args()
    if args.self_test:
        self_test()
        return 0

    questions = yaml.safe_load(Path(args.questions).read_text(encoding="utf-8"))
    results = run(questions, args.retrieval_only)
    summary = summarize(results)
    report = {
        "date": date.today().isoformat(),
        "retrieval_only": args.retrieval_only,
        "top_k": int(os.getenv("RETRIEVAL_TOP_K", "3")),
        "summary": summary,
        "results": [r.__dict__ for r in results],
    }
    out = EVALS_DIR / "reports" / f"{report['date']}.json"
    out.parent.mkdir(exist_ok=True)
    out.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps(summary["overall"], indent=2), f"\nreport: {out}")

    if args.baseline:
        baseline = json.loads(Path(args.baseline).read_text(encoding="utf-8"))["summary"]
        bad = regressions(summary, baseline, float(os.getenv("EVAL_REGRESSION_TOLERANCE", "0.15")))
        for line in bad:
            print("REGRESSION", line)
        return 1 if bad else 0
    return 0


if __name__ == "__main__":
    sys.exit(main())
