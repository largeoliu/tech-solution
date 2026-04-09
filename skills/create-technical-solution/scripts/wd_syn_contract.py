from __future__ import annotations

import re


WD_SYN_REQUIRED_FRAGMENTS = [
    "#### 候选方案对比",
    "| 复用 |",
    "| 改造 |",
    "| 新建 |",
    "#### 选定路径",
    "关键证据引用",
]


def required_fragments() -> list[str]:
    return list(WD_SYN_REQUIRED_FRAGMENTS)


def required_slot_fragments(title: str) -> list[str]:
    return [
        f"### 槽位：{title}",
        "#### 目标能力",
        "- <本槽位要承载的能力或结论>",
        "#### 候选方案对比",
        "| 路径 | 可行性 | 关键证据 | 选择理由 |",
        "|------|--------|----------|----------|",
        "| 复用 |",
        "| 改造 |",
        "| 新建 |",
        "#### 选定路径",
        "- 路径:",
        "- 选定写法:",
        "- 关键证据引用:",
        f"- 建议落位槽位: {title}",
        "- 模板承载缺口:",
        "- 未决问题:",
    ]


def render_slot_lines(title: str) -> list[str]:
    return required_slot_fragments(title)


def target_capability_present(slot_block: str) -> bool:
    match = re.search(r"^####\s+目标能力\s*$", slot_block, re.MULTILINE)
    if not match:
        return False
    remainder = slot_block[match.end():]
    next_subsection = re.search(r"^####\s+", remainder, re.MULTILINE)
    section = remainder[: next_subsection.start()] if next_subsection else remainder
    for line in section.splitlines():
        stripped = line.strip()
        if stripped.startswith("- ") and len(stripped) > 2:
            return True
    return False


def missing_fragments(block: str) -> list[str]:
    return [fragment for fragment in WD_SYN_REQUIRED_FRAGMENTS if fragment not in block]


def missing_slot_fragments(block: str, title: str) -> list[str]:
    missing: list[str] = []
    for fragment in required_slot_fragments(title):
        if fragment == "- <本槽位要承载的能力或结论>":
            continue
        if fragment not in block:
            missing.append(fragment)
    return missing
