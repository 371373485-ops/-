from dataclasses import dataclass

from app.schemas.diagnosis import (
    CredibilityReview,
    DiagnosisRequest,
    EvidenceBasedIssue,
    EvidenceFinding,
    MissingUserInput,
    PriorityAction,
    ReaderReactionSimulation,
    StructureAnalysis,
    TopBlocker,
)


PAIN_WORDS = ("痛点", "踩坑", "避坑", "不会", "别再", "问题", "失败", "焦虑", "后悔", "纠结")
VALUE_WORDS = ("步骤", "清单", "对比", "实测", "经验", "总结", "原因", "方法", "细节", "场景", "模板", "检查")
TRUST_WORDS = ("我", "真实", "亲测", "记录", "发现", "复盘", "踩坑", "对比", "试过")
DETAIL_WORDS = ("使用", "用了", "时间", "天", "周", "场景", "因为", "过程", "步骤", "对比", "条件", "适合", "不适合", "限制")
EMOTION_WORDS = ("焦虑", "后悔", "惊喜", "崩溃", "喜欢", "安心", "终于", "纠结", "担心")
ACTION_WORDS = ("评论", "留言", "收藏", "关注", "你觉得", "你会", "欢迎", "告诉我")
RISK_WORDS = ("绝对", "保证", "稳赚", "包治", "全网最好", "永久有效", "加微信", "私信领取")


@dataclass
class EvidenceBasedDiagnosisReport:
    top_3_blockers: list[TopBlocker]
    evidence_based_issues: list[EvidenceBasedIssue]
    reader_reaction_simulation: ReaderReactionSimulation
    structure_analysis: StructureAnalysis
    credibility_review: CredibilityReview
    missing_user_inputs: list[MissingUserInput]
    evidence_findings: list[EvidenceFinding]
    priority_actions: list[PriorityAction]


class EvidenceBasedDiagnosisAgent:
    name = "EvidenceBasedDiagnosisAgent"

    def run(self, payload: DiagnosisRequest) -> EvidenceBasedDiagnosisReport:
        issues = self._build_issues(payload)
        if not issues:
            issues = [self._positive_but_evidence_based_issue(payload)]
        top_3 = self._top_3(issues)
        findings = self._legacy_findings(issues)
        return EvidenceBasedDiagnosisReport(
            top_3_blockers=top_3,
            evidence_based_issues=issues,
            reader_reaction_simulation=self._reader_reaction(payload, issues),
            structure_analysis=self._structure_analysis(payload),
            credibility_review=self._credibility_review(payload),
            missing_user_inputs=self._missing_user_inputs(payload),
            evidence_findings=findings,
            priority_actions=self._priority_actions(findings),
        )

    def _build_issues(self, payload: DiagnosisRequest) -> list[EvidenceBasedIssue]:
        issues: list[EvidenceBasedIssue] = []
        title = payload.title
        content = payload.content
        cover = payload.cover_text or ""
        comment = payload.comment_guide or ""
        tags = "、".join(payload.tags) if payload.tags else "未提供标签"

        risk_hits = [word for word in RISK_WORDS if word in f"{title}\n{content}\n{cover}\n{comment}"]
        if risk_hits:
            issues.append(
                EvidenceBasedIssue(
                    field="risk_expression",
                    original_excerpt="、".join(risk_hits),
                    issue="存在绝对化、夸大承诺或疑似违规引流表达。",
                    why_it_matters="这类表达会降低信任，并可能带来合规风险。",
                    impact_area="compliance",
                    severity="high",
                    rewrite_principle="改成经验分享、适用边界和人工复核提醒，不承诺确定结果。",
                    example_fix="基于我的这次复盘，这些做法有参考价值，但不同场景结果会有差异。",
                )
            )

        if self._is_generic_title(payload):
            issues.append(
                EvidenceBasedIssue(
                    field="title",
                    original_excerpt=self._snippet(title),
                    issue="标题没有快速交代目标读者、具体场景或可获得的信息。",
                    why_it_matters="读者在信息流里先看标题；如果看不出“和我有什么关系”，点击意愿会下降。",
                    impact_area="click",
                    severity="high",
                    rewrite_principle="用目标人群、具体场景和可验证的信息形式重写标题，不承诺确定效果。",
                    example_fix=f"{payload.target_audience}做{payload.category}前，先看这 3 个发布前检查点",
                )
            )

        opening = self._first_lines(content)
        if not self._mentions_audience(opening, payload) or not self._contains_any(opening, PAIN_WORDS + VALUE_WORDS + ("先说结论",)):
            issues.append(
                EvidenceBasedIssue(
                    field="body.opening",
                    original_excerpt=self._snippet(opening),
                    issue="开头 3 秒没有快速交代适合谁、为什么要继续看、能获得什么。",
                    why_it_matters="读者进入正文后会先判断是否值得继续读；价值点出现太晚，会影响完读和收藏。",
                    impact_area="completion",
                    severity="high",
                    rewrite_principle="第一段先写目标读者、具体问题和结论，再展开步骤。",
                    example_fix=f"如果你是{payload.target_audience}，正在纠结{payload.category}怎么判断，先看这 3 点。",
                )
            )

        if not self._has_clear_structure(content):
            issues.append(
                EvidenceBasedIssue(
                    field="body.structure",
                    original_excerpt=self._snippet(content),
                    issue="正文缺少清晰分段、编号或层级，读者不容易扫读到重点。",
                    why_it_matters="发布前内容需要便于扫读、完读和收藏；结构不清会削弱信息效率。",
                    impact_area="completion",
                    severity="medium",
                    rewrite_principle="拆成短段，并用 1/2/3 或小标题呈现判断标准、步骤和适用提醒。",
                    example_fix="1. 先判断自己的场景；2. 再对比关键条件；3. 最后写适用和不适用提醒。",
                )
            )

        if not self._contains_any(content, TRUST_WORDS) or not self._has_detail_evidence(content):
            issues.append(
                EvidenceBasedIssue(
                    field="body.trust_details",
                    original_excerpt=self._snippet(content),
                    issue="可信细节不足，缺少真实场景、对比过程、限制条件或体验细节。",
                    why_it_matters="只有结论但缺少过程证据，会让读者怀疑这是泛经验或广告话术。",
                    impact_area="trust",
                    severity="high",
                    rewrite_principle="只补充用户真实经历和可公开细节；没有提供时必须先索取，不能编造。",
                    example_fix="模板：我在【真实场景】里用了【时间/频次】，对比了【对象】，发现【真实观察】，但【限制条件】下不一定适用。",
                )
            )

        if payload.goal in ("种草", "转化") and not self._contains_any(content, ("适合", "不适合", "预算", "需求", "限制", "场景")):
            issues.append(
                EvidenceBasedIssue(
                    field="body.boundary",
                    original_excerpt=self._snippet(content),
                    issue="种草/转化目标缺少适用边界和选择依据，容易显得像直接推荐。",
                    why_it_matters="边界越清楚，读者越容易判断是否适合自己，也能降低夸大宣传风险。",
                    impact_area="trust",
                    severity="medium",
                    rewrite_principle="补充适合谁、不适合谁、选择标准或谨慎参考条件。",
                    example_fix="更适合【真实人群/场景】，如果你是【限制条件】，建议先谨慎对比。",
                )
            )

        if not payload.tags or len(payload.tags) < 3 or payload.category not in tags:
            issues.append(
                EvidenceBasedIssue(
                    field="tags",
                    original_excerpt=tags,
                    issue="标签没有充分覆盖赛道、人群和内容形式。",
                    why_it_matters="标签会影响读者对内容边界的识别，过少或过泛会降低匹配效率。",
                    impact_area="interaction",
                    severity="low",
                    rewrite_principle="保留真实相关标签，补齐赛道、人群、内容形式和目标标签。",
                    example_fix=f"#{payload.category} #{payload.target_audience} #经验分享 #发布前检查",
                )
            )

        if cover and not self._contains_any(cover, PAIN_WORDS + VALUE_WORDS + (payload.category,)):
            issues.append(
                EvidenceBasedIssue(
                    field="cover_text",
                    original_excerpt=self._snippet(cover),
                    issue="封面文案没有承接标题里的问题或价值点。",
                    why_it_matters="封面是点击前的第二判断点，信息弱会让标题和封面无法互相补强。",
                    impact_area="click",
                    severity="medium",
                    rewrite_principle="封面只放一个最强判断点，优先呈现场景、清单或避坑。",
                    example_fix=f"{payload.category}发布前检查",
                )
            )

        if not self._contains_any(f"{content}\n{comment}", ACTION_WORDS):
            issues.append(
                EvidenceBasedIssue(
                    field="comment_guide",
                    original_excerpt=self._snippet(comment or "未提供评论引导"),
                    issue="缺少合规的站内互动引导。",
                    why_it_matters="读者读完后没有明确回应入口，评论互动和后续选题反馈会偏弱。",
                    impact_area="interaction",
                    severity="low",
                    rewrite_principle="用开放问题引导站内评论，不诱导站外私信、加微信或提交隐私。",
                    example_fix="你现在最纠结哪一步？可以在评论区说说你的真实情况。",
                )
            )
        return issues

    def _missing_user_inputs(self, payload: DiagnosisRequest) -> list[MissingUserInput]:
        checks = [
            ("真实场景", ("场景", "上班", "通勤", "早上", "晚上", "出门", "会议", "学习"), "这个经验来自什么真实场景？"),
            ("观察/使用周期", ("用了", "使用", "观察", "天", "周", "月", "小时", "连续"), "你观察/使用了多久？"),
            ("记录到的变化", ("记录", "变化", "之前", "后来", "前后", "发现", "对比"), "你记录了哪些变化？"),
            ("失败或不适用情况", ("失败", "不适合", "踩坑", "无效", "没用", "限制", "前提", "谨慎", "因人而异"), "有没有失败或不适用情况？"),
            ("适合/不适合人群", (payload.target_audience, "适合", "不适合", "新手", "小白", "上班族", "学生", "宝妈"), "适合什么人，不适合什么人？"),
            ("不可公开信息边界", ("不能公开", "不方便公开", "隐私", "脱敏", "客户数据", "账号", "姓名", "手机号"), "有没有不能公开的信息？如有，请只提供可公开或已脱敏细节。"),
            ("真实体验依据", ("我", "真实", "亲测", "记录", "发现", "踩坑", "复盘"), "请补充你的真实体验、过程或复盘依据。"),
        ]
        missing = []
        for field, keywords, prompt in checks:
            if not self._contains_any(payload.content, keywords):
                missing.append(
                    MissingUserInput(
                        field=field,
                        reason=f"原文没有提供{field}，系统不能替用户编造。",
                        suggested_prompt=prompt,
                    )
                )
        return missing

    def _reader_reaction(self, payload: DiagnosisRequest, issues: list[EvidenceBasedIssue]) -> ReaderReactionSimulation:
        opening = self._first_lines(payload.content)
        title_issue = next((issue for issue in issues if issue.field == "title"), None)
        return ReaderReactionSimulation(
            title_first_impression=(
                f"读者看到“{self._snippet(payload.title, 50)}”会先判断是否和自己有关。"
                if not title_issue
                else f"读者看到“{self._snippet(payload.title, 50)}”可能觉得主题存在，但具体收益和适合谁还不够明确。"
            ),
            after_first_three_lines=f"读完开头“{self._snippet(opening, 70)}”后，读者会寻找具体步骤、真实依据和适用边界。",
            likely_drop_off_reason=issues[0].why_it_matters,
            strongest_interest_point=f"最能吸引{payload.target_audience}的是和“{payload.category}”直接相关的真实场景、踩坑或清单。",
            information_to_frontload=["适合谁", "先说结论", "真实场景", "具体步骤", "限制条件"],
        )

    def _structure_analysis(self, payload: DiagnosisRequest) -> StructureAnalysis:
        content = payload.content
        return StructureAnalysis(
            opening_hook="开头能较快进入主题。" if self._contains_any(self._first_lines(content), PAIN_WORDS + VALUE_WORDS + ("先说结论",)) else "开头 3 秒没有足够快地给出读者、痛点或结论。",
            information_hierarchy="正文已有步骤或分段。" if self._has_clear_structure(content) else "正文层级偏平，需要拆成短段、编号和小结。",
            trust_building="已有个人视角或复盘信号。" if self._contains_any(content, TRUST_WORDS) else "缺少个人视角、复盘背景或过程依据。",
            detail_evidence="已有一定细节证据。" if self._has_detail_evidence(content) else "缺少使用时间、场景、对比、限制条件或真实体验细节。",
            emotional_resonance="已有情绪共鸣词。" if self._contains_any(content, EMOTION_WORDS + PAIN_WORDS) else "情绪共鸣偏弱，读者不容易产生“这说的是我”的感觉。",
            action_guidance="已有站内行动引导。" if self._contains_any(f"{content}\n{payload.comment_guide or ''}", ACTION_WORDS) else "缺少合规站内评论或收藏引导。",
        )

    def _credibility_review(self, payload: DiagnosisRequest) -> CredibilityReview:
        text = f"{payload.title}\n{payload.content}\n{payload.cover_text or ''}\n{payload.comment_guide or ''}"
        missing = []
        strong = []
        if self._contains_any(text, TRUST_WORDS):
            strong.append("存在个人视角或复盘表达")
        else:
            missing.append("个人视角或真实复盘背景")
        if self._has_detail_evidence(payload.content):
            strong.append("存在步骤、场景或条件类细节")
        else:
            missing.append("使用时间、场景、对比、限制条件或真实体验细节")
        if self._mentions_audience(text, payload):
            strong.append("提到目标人群或相近人群")
        else:
            missing.append("目标读者的具体状态")
        sounds_like_ad = self._contains_any(text, ("推荐", "入手", "必买", "全网最好", "保证", "绝对"))
        suggestions = [f"补充{item}，只能使用用户真实信息。" for item in missing]
        if sounds_like_ad:
            suggestions.append("降低广告感，改为经验分享和适用边界。")
        return CredibilityReview(
            is_too_generic=len(payload.content) < 120 or len(missing) >= 2,
            sounds_like_ad=sounds_like_ad,
            missing_trust_signals=missing,
            strong_trust_signals=strong,
            suggestions=suggestions,
        )

    def _top_3(self, issues: list[EvidenceBasedIssue]) -> list[TopBlocker]:
        severity_rank = {"high": 0, "medium": 1, "low": 2}
        impact_rank = {"compliance": 0, "click": 1, "completion": 2, "trust": 3, "interaction": 4}
        sorted_issues = sorted(issues, key=lambda issue: (severity_rank[issue.severity], impact_rank[issue.impact_area]))
        return [
            TopBlocker(
                rank=index + 1,
                field=issue.field,
                issue=issue.issue,
                evidence=issue.original_excerpt,
                severity=issue.severity,
                why_it_blocks=issue.why_it_matters,
                suggested_focus=issue.rewrite_principle,
            )
            for index, issue in enumerate(sorted_issues[:3])
        ]

    def _legacy_findings(self, issues: list[EvidenceBasedIssue]) -> list[EvidenceFinding]:
        priority_by_severity = {"high": "P0", "medium": "P1", "low": "P2"}
        dimension_by_impact = {
            "click": "点击",
            "completion": "完读",
            "trust": "信任",
            "interaction": "互动",
            "compliance": "合规/信任",
        }
        return [
            EvidenceFinding(
                priority=priority_by_severity[issue.severity],
                dimension=dimension_by_impact[issue.impact_area],
                source=issue.field,
                evidence=issue.original_excerpt,
                issue=issue.issue,
                impact=issue.why_it_matters,
                action=issue.rewrite_principle,
            )
            for issue in issues[:6]
        ]

    def _priority_actions(self, findings: list[EvidenceFinding]) -> list[PriorityAction]:
        priority_order = {"P0": 0, "P1": 1, "P2": 2, "P3": 3}
        selected = sorted(findings, key=lambda item: priority_order[item.priority])[:5]
        return [
            PriorityAction(
                priority=index + 1,
                action=item.action,
                reason=f"{item.source}证据显示：{item.issue}",
                expected_effect=f"优先改善{item.dimension}。{item.impact}",
            )
            for index, item in enumerate(selected)
        ]

    def _positive_but_evidence_based_issue(self, payload: DiagnosisRequest) -> EvidenceBasedIssue:
        return EvidenceBasedIssue(
            field="body",
            original_excerpt=self._snippet(payload.content),
            issue="当前内容基础较完整，但还可以补充更多真实条件和适用边界。",
            why_it_matters="真实细节越充分，读者越容易判断内容是否值得信任和收藏。",
            impact_area="trust",
            severity="low",
            rewrite_principle="保留现有结构，继续补充用户真实经历、时间、场景和限制条件。",
            example_fix="在对应步骤后补一句：这是我在【真实场景】下的观察，【限制条件】下需要谨慎参考。",
        )

    def _is_generic_title(self, payload: DiagnosisRequest) -> bool:
        title = payload.title
        return (
            len(title) < 10
            or not self._mentions_audience(title, payload)
            or not any(char.isdigit() for char in title)
            or not self._contains_any(title, PAIN_WORDS + VALUE_WORDS)
        )

    def _mentions_audience(self, text: str, payload: DiagnosisRequest) -> bool:
        target = payload.target_audience
        compact_target = target.replace("人群", "").replace("用户", "").replace("人", "")
        return bool(target and target in text) or bool(compact_target and compact_target in text)

    def _has_clear_structure(self, content: str) -> bool:
        paragraphs = [part for part in content.splitlines() if part.strip()]
        return len(paragraphs) >= 3 or self._contains_any(content, ("1.", "2.", "①", "②", "第一", "第二", "- "))

    def _has_detail_evidence(self, content: str) -> bool:
        return len(content) >= 180 or self._contains_any(content, DETAIL_WORDS)

    def _first_lines(self, content: str) -> str:
        parts = [part.strip() for part in content.splitlines() if part.strip()]
        return "\n".join(parts[:3]) if parts else content[:120]

    def _snippet(self, text: str, limit: int = 90) -> str:
        compact = " ".join((text or "").split())
        if not compact:
            return "未提供"
        if len(compact) <= limit:
            return compact
        return compact[: limit - 3].rstrip() + "..."

    def _contains_any(self, text: str, words: tuple[str, ...]) -> bool:
        return any(word and word in text for word in words)
