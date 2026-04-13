from __future__ import annotations

import hashlib
import re


PLACEHOLDER_PATTERNS = [
    re.compile(r"承载.+技术结论"),
    re.compile(r"需求地址"),
    re.compile(r"Redmine地址", re.IGNORECASE),
    re.compile(r"对接三方接口文档"),
    re.compile(r"<待补充>"),
    re.compile(r"<一句话写法>"),
    re.compile(r"<复用\s*/\s*改造\s*/\s*新建>"),
    re.compile(r"<若无则写无>"),
    re.compile(r"<本槽位要承载的能力或结论>"),
]


def placeholder_hits(text: str) -> list[str]:
    hits: list[str] = []
    for pattern in PLACEHOLDER_PATTERNS:
        for match in pattern.finditer(text):
            hit = match.group(0).strip()
            if hit and hit not in hits:
                hits.append(hit)
    return hits


def normalized_slot_body(slot_block: str, title: str) -> str:
    text = slot_block.replace(f"### 槽位：{title}", "### 槽位：<TITLE>")
    text = text.replace(f"- 建议落位槽位: {title}", "- 建议落位槽位: <TITLE>")
    text = re.sub(r"\s+", " ", text).strip()
    return text


def repeated_slot_groups(slot_blocks: dict[str, str]) -> list[dict[str, object]]:
    titles = list(slot_blocks.keys())
    normalized = {title: normalized_slot_body(block, title) for title, block in slot_blocks.items()}
    exact_groups: dict[str, list[str]] = {}
    for title, body in normalized.items():
        digest = hashlib.sha256(body.encode("utf-8")).hexdigest()
        exact_groups.setdefault(digest, []).append(title)

    findings: list[dict[str, object]] = [
        {"type": "exact", "titles": titles_group}
        for titles_group in exact_groups.values()
        if len(titles_group) >= 2
    ]
    return findings


INTERMEDIATE_FIELD_PATTERNS = [
    re.compile(r"####\s*候选方案对比"),
    re.compile(r"关键证据引用"),
    re.compile(r"模板承载缺口"),
    re.compile(r"未决问题"),
]


def intermediate_field_hits(text: str) -> list[str]:
    hits: list[str] = []
    for pattern in INTERMEDIATE_FIELD_PATTERNS:
        for match in pattern.finditer(text):
            hit = match.group(0).strip()
            if hit and hit not in hits:
                hits.append(hit)
    return hits
