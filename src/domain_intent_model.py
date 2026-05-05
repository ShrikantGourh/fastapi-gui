from __future__ import annotations

from dataclasses import dataclass, asdict
from pathlib import Path
import json
import re
from collections import Counter, defaultdict


TOKEN_RE = re.compile(r"[a-z0-9]+")


@dataclass
class DetectionResult:
    domain: str
    intent: str
    operation: str
    agent_type: str
    answer: str


class DomainIntentRouter:
    def __init__(self, samples: list[dict], token_stats: dict):
        self.samples = samples
        self.token_stats = token_stats

    @staticmethod
    def _tokenize(text: str) -> list[str]:
        return TOKEN_RE.findall((text or "").lower())

    def _score_sample(self, question_tokens: list[str], sample: dict) -> float:
        stokens = set(self._tokenize(sample.get("QUESTION_TEXT", "") + " " + sample.get("CONTEXT", "")))
        if not stokens:
            return 0.0
        overlap = len(stokens.intersection(question_tokens))
        return overlap / (len(stokens) ** 0.5)

    def detect(self, question: str) -> DetectionResult:
        qtokens = self._tokenize(question)
        scored = sorted(((self._score_sample(qtokens, s), s) for s in self.samples), key=lambda x: x[0], reverse=True)
        best_score, best = scored[0]

        if best_score == 0:
            return DetectionResult(
                domain="generic",
                intent="unknown",
                operation="read",
                agent_type="api_agent",
                answer="I could not confidently detect your request. Please add more specific keywords.",
            )

        answer = (best.get("CONTEXT") or "").strip() or f"Matched {best['INTENT']} in {best['DOMAIN']}"
        return DetectionResult(
            domain=best["DOMAIN"],
            intent=best["INTENT"],
            operation=best["OPERATION"],
            agent_type=best["AGENT_TYPE"],
            answer=answer,
        )

    def save(self, path: str | Path) -> None:
        payload = {"samples": self.samples, "token_stats": self.token_stats}
        Path(path).write_text(json.dumps(payload, indent=2), encoding="utf-8")

    @classmethod
    def load(cls, path: str | Path) -> "DomainIntentRouter":
        payload = json.loads(Path(path).read_text(encoding="utf-8"))
        return cls(payload["samples"], payload.get("token_stats", {}))


def train_router(samples: list[dict]) -> DomainIntentRouter:
    token_counts: dict[str, Counter] = defaultdict(Counter)
    for row in samples:
        key = f"{row['DOMAIN']}|{row['INTENT']}|{row['OPERATION']}|{row['AGENT_TYPE']}"
        token_counts[key].update(DomainIntentRouter._tokenize((row.get("QUESTION_TEXT", "") + " " + row.get("CONTEXT", ""))))

    token_stats = {k: dict(v.most_common(10)) for k, v in token_counts.items()}
    return DomainIntentRouter(samples, token_stats)


def parse_training_csv(path: str | Path) -> list[dict]:
    lines = Path(path).read_text(encoding="utf-8").splitlines()
    header = [h.strip() for h in lines[0].split(",")]
    data: list[dict] = []
    for line in lines[1:]:
        values = [v.strip() for v in line.split(",")]
        if len(values) != len(header):
            continue
        data.append(dict(zip(header, values)))
    return data


def result_to_dict(result: DetectionResult) -> dict:
    return asdict(result)
