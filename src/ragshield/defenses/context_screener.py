"""Label-free context screening for the full SafeRAG defense condition."""

from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass

from ragshield.retrieval.sanitizer import unsafe_reasons
from ragshield.retrieval.vector_store import tokenize


CHINESE_RISK_PATTERNS = {
    "answer_suppression": re.compile(
        r"(?:不要|禁止|无需|不得|请勿).{0,12}(?:回答|作答|回复|提供)|"
        r"(?:拒绝回答|无法回答|停止回答|直接拒答|输出[“\"']?拒答)"
    ),
    "embedded_instruction": re.compile(
        r"(?:忽略|绕过|覆盖|取代).{0,16}(?:指令|要求|规则|提示词)|"
        r"(?:系统消息|开发者消息|最高优先级)"
    ),
    "promotion_signal": re.compile(
        r"(?:广告|赞助|推广|强烈推荐|官方指定|独家合作|技术支持[:：]|"
        r"首选平台|品牌合作)|"
        r"(?:支持|鼓励).{0,24}(?:平台|品牌).{0,16}(?:推广|普及|合作)"
    ),
    "tool_or_exfiltration": re.compile(
        r"(?:调用|执行|运行).{0,12}(?:工具|命令|接口)|"
        r"(?:发送|上传|泄露).{0,16}(?:密钥|隐私|机密|数据)"
    ),
}


@dataclass(frozen=True)
class ScreeningDecision:
    context_hash: str
    kept: bool
    reasons: tuple[str, ...]
    relevance: float


def _hash(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()[:16]


def _token_set(text: str) -> set[str]:
    return set(tokenize(text))


def _jaccard(left: set[str], right: set[str]) -> float:
    union = left | right
    return len(left & right) / len(union) if union else 0.0


def _relevance(question_tokens: set[str], text: str) -> float:
    text_tokens = _token_set(text)
    return _jaccard(question_tokens, text_tokens)


def context_risk_reasons(text: str) -> list[str]:
    reasons = list(unsafe_reasons(text))
    reasons.extend(name for name, pattern in CHINESE_RISK_PATTERNS.items() if pattern.search(text))
    return sorted(set(reasons))


def screen_contexts(
    question: str,
    contexts: list[str],
    duplicate_threshold: float = 0.96,
) -> tuple[list[str], list[ScreeningDecision]]:
    """Remove explicit attacks and near-duplicate contexts without benchmark labels."""

    question_tokens = _token_set(question)
    candidates = []
    for index, text in enumerate(contexts):
        reasons = context_risk_reasons(text)
        candidates.append(
            {
                "index": index,
                "text": text,
                "tokens": _token_set(text),
                "relevance": _relevance(question_tokens, text),
                "reasons": reasons,
            }
        )

    candidates.sort(key=lambda item: (bool(item["reasons"]), -item["relevance"], item["index"]))
    kept = []
    kept_tokens: list[set[str]] = []
    decisions: dict[int, ScreeningDecision] = {}
    for item in candidates:
        reasons = list(item["reasons"])
        duplicate = any(
            _jaccard(item["tokens"], existing) >= duplicate_threshold
            for existing in kept_tokens
        )
        if duplicate:
            reasons.append("near_duplicate")
        should_keep = not reasons
        if should_keep:
            kept.append(item["text"])
            kept_tokens.append(item["tokens"])
        decisions[item["index"]] = ScreeningDecision(
            context_hash=_hash(item["text"]),
            kept=should_keep,
            reasons=tuple(sorted(set(reasons))),
            relevance=round(item["relevance"], 6),
        )

    if not kept and candidates:
        fallback = min(candidates, key=lambda item: (len(item["reasons"]), -item["relevance"]))
        kept.append(fallback["text"])
        previous = decisions[fallback["index"]]
        decisions[fallback["index"]] = ScreeningDecision(
            context_hash=previous.context_hash,
            kept=True,
            reasons=tuple(sorted(set(previous.reasons + ("fallback_retained",)))),
            relevance=previous.relevance,
        )

    ordered_decisions = [decisions[index] for index in range(len(contexts))]
    return kept, ordered_decisions
