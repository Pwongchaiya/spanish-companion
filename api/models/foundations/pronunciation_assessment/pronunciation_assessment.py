"""Pronunciation assessment result models (Azure Pronunciation Assessment, roadmap Phase 4 B1)."""

from dataclasses import dataclass


@dataclass
class PhonemeScore:
    phoneme: str
    accuracy_score: float


@dataclass
class WordScore:
    word: str
    accuracy_score: float | None  # invalid/absent when error_type is "Omission"
    error_type: str  # "None" | "Omission" | "Insertion" | "Mispronunciation", passed through as Azure emits it
    phonemes: list[PhonemeScore]


@dataclass
class PronunciationAssessment:
    accuracy_score: float
    fluency_score: float
    completeness_score: float
    pronunciation_score: float
    prosody_score: float | None  # Azure supports prosody for en-US only; None for es-ES is normal
    words: list[WordScore]
