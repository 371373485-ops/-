from app.schemas.case import MatchedSample
from app.schemas.diagnosis import DiagnosisRequest, SampleInsight


NO_SAMPLE_CAUTION = "当前没有匹配到用户自有或授权样本；样本仅供结构参考，不代表平台表现。"
SAMPLE_CAUTION = "样本仅供结构参考，不代表平台表现；请使用自己的真实经历、证据和表达边界重新创作，不使用样本中的账号、隐私或平台数据作为承诺。"


def build_sample_insights(matched_samples: list[MatchedSample], current_payload: DiagnosisRequest) -> SampleInsight:
    if not matched_samples:
        return SampleInsight(
            sample_count=0,
            reusable_structures=[],
            opening_patterns=[],
            title_patterns=[],
            trust_signals=[],
            caution=NO_SAMPLE_CAUTION,
        )

    reusable_structures = _unique(
        _structure_from_learn_point(point)
        for sample in matched_samples
        for point in sample.what_to_learn
    )
    title_patterns = _unique(_title_pattern(sample.title, current_payload) for sample in matched_samples)
    opening_patterns = _unique(_opening_pattern(sample) for sample in matched_samples)
    trust_signals = _unique(
        signal
        for sample in matched_samples
        for signal in _trust_signals(sample)
    )

    return SampleInsight(
        sample_count=len(matched_samples),
        reusable_structures=reusable_structures[:5] or ["先交代目标人群和场景，再拆解判断点，最后补充适用边界。"],
        opening_patterns=opening_patterns[:5] or ["开头先点明目标读者、当前困扰和本篇能帮助判断的内容。"],
        title_patterns=title_patterns[:5] or [f"{current_payload.target_audience} + {current_payload.category}场景 + 可复用清单/步骤"],
        trust_signals=trust_signals[:5] or ["用真实场景、过程记录、适用/不适用条件建立信任。"],
        caution=SAMPLE_CAUTION,
    )


def _structure_from_learn_point(point: str) -> str:
    if "标题" in point or "关键词" in point:
        return "标题先明确人群、场景和信息形式，正文再承接具体判断。"
    if "标签" in point:
        return "标签覆盖赛道、人群和内容形式，避免只堆泛标签。"
    if "段落" in point or "步骤" in point or "正文" in point:
        return "正文按短段或编号组织，每段只处理一个判断点。"
    if "痛点" in point:
        return "开头先写目标读者的具体困扰，再给出可执行的判断路径。"
    return "提炼样本的信息组织方式，再替换为自己的真实经历和具体细节。"


def _title_pattern(title: str, payload: DiagnosisRequest) -> str:
    has_number = any(char.isdigit() for char in title)
    if "清单" in title:
        return f"{payload.target_audience} + {payload.category} + 清单式标题"
    if "避坑" in title or "踩坑" in title:
        return f"{payload.target_audience} + 常见误区/避坑提醒 + 具体场景"
    if "新手" in title or "小白" in title:
        return "目标人群前置 + 入门判断 + 低门槛表达"
    if has_number:
        return "目标场景 + 数字化检查点 + 明确内容边界"
    return "人群/场景前置 + 明确信息类型 + 保守表达"


def _opening_pattern(sample: MatchedSample) -> str:
    learn_text = " ".join(sample.what_to_learn + [sample.suggested_adaptation, sample.similarity_reason])
    if "痛点" in learn_text:
        return "先写读者正在遇到的问题，再说明本文只提供结构化参考。"
    if "步骤" in learn_text or "段落" in learn_text:
        return "开头先给结论，再用编号展开步骤。"
    if "标签" in learn_text:
        return "开头明确赛道和读者对象，降低读者判断成本。"
    return "先说明适合谁和使用场景，再进入具体判断。"


def _trust_signals(sample: MatchedSample) -> list[str]:
    text = " ".join(sample.what_to_learn + [sample.suggested_adaptation, sample.similarity_reason, sample.caution])
    signals: list[str] = []
    if any(word in text for word in ("真实", "经历", "经验")):
        signals.append("真实经历或经验视角")
    if any(word in text for word in ("结构", "段落", "步骤", "清单")):
        signals.append("清晰步骤或清单结构")
    if any(word in text for word in ("标签", "赛道", "人群")):
        signals.append("赛道、人群和内容形式边界清楚")
    if any(word in text for word in ("合规", "边界", "不要复制", "不要照搬")):
        signals.append("明确提示不能直接复制样本表达")
    return signals


def _unique(items) -> list[str]:
    result: list[str] = []
    for item in items:
        if item and item not in result:
            result.append(item)
    return result
