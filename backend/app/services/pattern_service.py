import re
from collections import Counter, defaultdict
from statistics import mean
from typing import Any

from app.models.database import get_connection, init_db
from app.schemas.pattern import (
    CategoryPatternSummary,
    FrequencyItem,
    OpeningStructureCount,
    PatternAnalysisResponse,
    StructureCount,
    TitleLengthBucket,
)
from app.schemas.sample import SampleItem
from app.services.sample_service import row_to_sample


TITLE_KEYWORDS = (
    "新手",
    "避坑",
    "清单",
    "教程",
    "攻略",
    "真实",
    "实测",
    "亲测",
    "普通人",
    "小白",
    "收藏",
    "对比",
    "方法",
    "技巧",
    "经验",
    "步骤",
    "结果",
    "反差",
    "别再",
    "建议",
)


def _round(value: float) -> float:
    return round(value, 4)


def _load_samples(category: str | None = None) -> list[SampleItem]:
    init_db()
    if category:
        sql = "SELECT * FROM samples WHERE category = ? ORDER BY id DESC"
        params: tuple[Any, ...] = (category,)
    else:
        sql = "SELECT * FROM samples ORDER BY id DESC"
        params = ()

    with get_connection() as connection:
        rows = connection.execute(sql, params).fetchall()
    return [row_to_sample(row) for row in rows]


def _title_keywords(samples: list[SampleItem]) -> list[FrequencyItem]:
    counter: Counter[str] = Counter()
    for sample in samples:
        title = sample.title
        for keyword in TITLE_KEYWORDS:
            if keyword in title:
                counter[keyword] += 1
        for token in re.findall(r"[A-Za-z0-9]+", title):
            if len(token) >= 2:
                counter[token.lower()] += 1
    return [FrequencyItem(value=value, count=count) for value, count in counter.most_common(12)]


def _tag_frequency(samples: list[SampleItem]) -> list[FrequencyItem]:
    counter: Counter[str] = Counter()
    for sample in samples:
        counter.update(sample.tags)
    return [FrequencyItem(value=value, count=count) for value, count in counter.most_common(12)]


def _title_length_distribution(samples: list[SampleItem]) -> list[TitleLengthBucket]:
    buckets = {
        "0-10": 0,
        "11-20": 0,
        "21-30": 0,
        "31-40": 0,
        "40+": 0,
    }
    for sample in samples:
        length = len(sample.title)
        if length <= 10:
            buckets["0-10"] += 1
        elif length <= 20:
            buckets["11-20"] += 1
        elif length <= 30:
            buckets["21-30"] += 1
        elif length <= 40:
            buckets["31-40"] += 1
        else:
            buckets["40+"] += 1
    return [TitleLengthBucket(bucket=bucket, count=count) for bucket, count in buckets.items()]


def _title_structure_flags(title: str) -> dict[str, bool]:
    return {
        "数字型": bool(re.search(r"\d", title)),
        "避坑型": any(word in title for word in ("避坑", "踩坑", "别再", "不要")),
        "清单型": any(word in title for word in ("清单", "合集", "列表")),
        "反差型": any(word in title for word in ("不是", "而是", "原来", "竟然", "反而", "但是")),
        "结果型": any(word in title for word in ("提升", "改善", "学会", "搞懂", "变好", "结果")),
        "教程型": any(word in title for word in ("教程", "攻略", "方法", "步骤", "指南")),
    }


def _title_structures(samples: list[SampleItem]) -> list[StructureCount]:
    total = max(len(samples), 1)
    counter: Counter[str] = Counter()
    for sample in samples:
        for name, matched in _title_structure_flags(sample.title).items():
            if matched:
                counter[name] += 1
    return [StructureCount(name=name, count=counter[name], ratio=_round(counter[name] / total)) for name in _title_structure_flags("").keys()]


def _opening_name(content: str) -> str:
    opening = next((part.strip() for part in content.splitlines() if part.strip()), content[:80])
    if any(word in opening for word in ("先说结论", "结论", "直接说")):
        return "结论先行"
    if any(word in opening for word in ("我", "亲测", "真实", "踩坑", "经历")):
        return "个人经历"
    if any(word in opening for word in ("你是不是", "有没有", "很多人", "新手")):
        return "痛点提问"
    if any(word in opening for word in ("适合", "写给", "给")):
        return "人群点名"
    return "普通开场"


def _opening_structures(samples: list[SampleItem]) -> list[OpeningStructureCount]:
    total = max(len(samples), 1)
    counter = Counter(_opening_name(sample.content) for sample in samples)
    order = ("结论先行", "个人经历", "痛点提问", "人群点名", "普通开场")
    return [OpeningStructureCount(name=name, count=counter[name], ratio=_round(counter[name] / total)) for name in order]


def _top_samples(samples: list[SampleItem]) -> list[SampleItem]:
    return sorted(samples, key=lambda item: item.likes + item.collects * 1.5 + item.comments * 2, reverse=True)[:10]


def _averages(samples: list[SampleItem]) -> tuple[float, float, float, float, float]:
    if not samples:
        return 0, 0, 0, 0, 0
    average_likes = mean(sample.likes for sample in samples)
    average_collects = mean(sample.collects for sample in samples)
    average_comments = mean(sample.comments for sample in samples)
    collect_rate = mean(sample.collects / max(sample.likes, 1) for sample in samples)
    comment_rate = mean(sample.comments / max(sample.likes, 1) for sample in samples)
    return (_round(average_likes), _round(average_collects), _round(average_comments), _round(collect_rate), _round(comment_rate))


def _style_summary(category: str, samples: list[SampleItem]) -> str:
    keywords = _title_keywords(samples)[:5]
    tags = _tag_frequency(samples)[:5]
    structures = [item.name for item in _title_structures(samples) if item.count > 0][:3]
    keyword_text = "、".join(item.value for item in keywords) or "暂无明显关键词"
    tag_text = "、".join(item.value for item in tags) or "暂无明显标签"
    structure_text = "、".join(structures) or "暂无明显标题结构"
    return f"{category}赛道样本更常出现 {keyword_text} 等标题关键词，标签集中在 {tag_text}，标题结构以 {structure_text} 为主。"


def _category_summaries(samples: list[SampleItem]) -> list[CategoryPatternSummary]:
    grouped: dict[str, list[SampleItem]] = defaultdict(list)
    for sample in samples:
        grouped[sample.category].append(sample)

    summaries: list[CategoryPatternSummary] = []
    for category, items in sorted(grouped.items()):
        average_likes, average_collects, average_comments, collect_rate, comment_rate = _averages(items)
        summaries.append(
            CategoryPatternSummary(
                category=category,
                sample_count=len(items),
                average_likes=average_likes,
                average_collects=average_collects,
                average_comments=average_comments,
                collect_rate=collect_rate,
                comment_rate=comment_rate,
                style_summary=_style_summary(category, items),
            )
        )
    return summaries


def analyze_patterns(category: str | None = None) -> PatternAnalysisResponse:
    samples = _load_samples(category)
    average_likes, average_collects, average_comments, collect_rate, comment_rate = _averages(samples)
    warning = "样本量不足，分析仅供参考。" if len(samples) < 5 else None

    return PatternAnalysisResponse(
        category=category,
        sample_count=len(samples),
        insufficient_sample_warning=warning,
        frequent_title_keywords=_title_keywords(samples),
        frequent_tags=_tag_frequency(samples),
        title_length_distribution=_title_length_distribution(samples),
        average_likes=average_likes,
        average_collects=average_collects,
        average_comments=average_comments,
        collect_rate=collect_rate,
        comment_rate=comment_rate,
        top_samples=_top_samples(samples),
        title_structures=_title_structures(samples),
        opening_structures=_opening_structures(samples),
        category_summaries=_category_summaries(samples),
    )
