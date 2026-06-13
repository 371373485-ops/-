import { useEffect, useState } from "react";
import {
  AlertTriangle,
  CheckCircle2,
  ChevronDown,
  ClipboardList,
  Copy,
  Eye,
  FileText,
  HelpCircle,
  Info,
  Layers3,
  ShieldAlert,
  Sparkles,
  UserRound,
} from "lucide-react";


async function copyText(text) {
  if (navigator.clipboard?.writeText) {
    await navigator.clipboard.writeText(text);
    return;
  }
  const textarea = document.createElement("textarea");
  textarea.value = text;
  textarea.setAttribute("readonly", "");
  textarea.style.position = "fixed";
  textarea.style.opacity = "0";
  document.body.appendChild(textarea);
  textarea.select();
  const copied = document.execCommand("copy");
  document.body.removeChild(textarea);
  if (!copied) throw new Error("复制失败，请手动选择文本复制。");
}


function asArray(value) {
  return Array.isArray(value) ? value : [];
}


const CONFIDENCE_LABELS = {
  high: "高",
  medium: "中",
  low: "低",
};

const SEVERITY_LABELS = {
  high: "高",
  medium: "中",
  low: "低",
};

const IMPACT_LABELS = {
  click: "点击判断",
  completion: "完读",
  collection: "收藏",
  trust: "信任",
  interaction: "互动",
  compliance: "合规",
};

const STAGE_LABELS = {
  feed: "信息流",
  title: "标题",
  opening: "开头",
  body: "正文",
  ending: "结尾",
  risk: "风险判断",
};

const LEGACY_TOP_BLOCKERS_LABEL = "Top 3 核心阻碍";


function labelFrom(map, value, fallback = "未知") {
  return map[value] || value || fallback;
}


function scoreBand(score) {
  const numericScore = Number(score);
  if (Number.isNaN(numericScore)) {
    return {
      label: "待评分",
      tone: "stone",
      text: "当前结果缺少可用总分，请优先查看必改任务和原文证据。",
    };
  }
  if (numericScore >= 85) {
    return {
      label: "基础较完整",
      tone: "low",
      text: "可以进入发布前微调，重点复核事实细节、合规边界和行动引导。",
    };
  }
  if (numericScore >= 70) {
    return {
      label: "需要重点优化",
      tone: "medium",
      text: "内容已有可用基础，但仍有影响点击、完读或信任的关键问题需要先处理。",
    };
  }
  return {
    label: "建议先重改",
    tone: "high",
    text: "发布前建议先完成核心结构、可信证据和风险表达修正，再考虑细节润色。",
  };
}


function fallbackScoreExplanation(score) {
  const band = scoreBand(score);
  return {
    score,
    band: band.label,
    interpretation: band.text,
    main_loss_factors: [],
    next_score_goal: "优先处理 Top 3 必改任务，再复核证据细节和合规表达。",
    disclaimer: "该分数是内容完整度与风险诊断分，不是流量预测，不承诺平台表现。",
  };
}


function CopyMiniButton({ text, label = "复制", onCopy }) {
  async function handleCopy() {
    try {
      await copyText(text);
      onCopy?.("已复制到剪贴板。");
    } catch (copyError) {
      onCopy?.(copyError.message || "复制失败，请手动选择文本复制。");
    }
  }

  return (
    <button
      type="button"
      onClick={handleCopy}
      className="inline-flex items-center gap-1 rounded-md border border-stone-300 px-2.5 py-1.5 text-xs font-semibold text-ink hover:border-stone-400"
    >
      <Copy className="h-3.5 w-3.5" />
      {label}
    </button>
  );
}


function ResultCard({ title, icon: Icon, children, action }) {
  return (
    <section className="rounded-lg border border-stone-200 bg-white p-5 shadow-sm">
      <div className="mb-4 flex items-center justify-between gap-3">
        <div className="flex items-center gap-2">
          {Icon && <Icon className="h-4 w-4 text-rosewood" />}
          <h2 className="text-base font-semibold text-ink">{title}</h2>
        </div>
        {action}
      </div>
      {children}
    </section>
  );
}


function AccordionSection({ title, icon: Icon, defaultOpen = false, children }) {
  const [open, setOpen] = useState(defaultOpen);

  return (
    <section className="rounded-lg border border-stone-200 bg-white shadow-sm">
      <button
        type="button"
        onClick={() => setOpen((current) => !current)}
        className="flex w-full items-center justify-between gap-3 px-4 py-4 text-left sm:px-5"
        aria-expanded={open}
      >
        <span className="flex min-w-0 items-center gap-2">
          {Icon && <Icon className="h-4 w-4 shrink-0 text-rosewood" />}
          <span className="truncate text-base font-semibold text-ink">{title}</span>
        </span>
        <ChevronDown className={`h-4 w-4 shrink-0 text-stone-500 transition-transform ${open ? "rotate-180" : ""}`} />
      </button>
      {open && <div className="border-t border-stone-100 px-4 py-4 sm:px-5">{children}</div>}
    </section>
  );
}


function Pill({ children, tone = "stone" }) {
  const tones = {
    stone: "bg-stone-100 text-stone-700",
    high: "bg-red-50 text-red-700",
    medium: "bg-amber-50 text-amber-700",
    low: "bg-mint/10 text-mint",
    ink: "bg-ink text-white",
  };
  return <span className={`rounded-md px-2 py-1 text-xs font-semibold ${tones[tone] || tones.stone}`}>{children}</span>;
}


function ScoreBar({ item }) {
  return (
    <div className="rounded-lg bg-stone-50 p-4">
      <div className="mb-1 flex items-center justify-between gap-3 text-sm">
        <span className="font-semibold text-ink">{item.name}</span>
        <span className="shrink-0 text-stone-600">{item.score}/100</span>
      </div>
      <div className="h-2 overflow-hidden rounded-full bg-stone-200">
        <div className="h-full rounded-full bg-mint" style={{ width: `${item.score}%` }} />
      </div>
      <p className="mt-2 text-xs leading-5 text-stone-500">{item.reason}</p>
    </div>
  );
}


function TextList({ items, emptyText }) {
  const list = asArray(items);
  if (list.length === 0) {
    return <p className="rounded-md bg-stone-50 p-3 text-sm text-stone-500">{emptyText}</p>;
  }
  return (
    <ul className="space-y-2 text-sm leading-6 text-stone-700">
      {list.map((item, index) => (
        <li key={`${item}-${index}`} className="flex gap-2">
          <CheckCircle2 className="mt-1 h-4 w-4 shrink-0 text-mint" />
          <span>{item}</span>
        </li>
      ))}
    </ul>
  );
}


function KeyValueGrid({ items }) {
  return (
    <div className="grid gap-3 md:grid-cols-2">
      {items.map(([label, value]) => (
        <div key={label} className="rounded-lg bg-stone-50 p-4">
          <p className="text-xs font-semibold text-stone-500">{label}</p>
          <p className="mt-2 text-sm leading-6 text-stone-700">{value || "暂无"}</p>
        </div>
      ))}
    </div>
  );
}


function FieldLine({ label, children }) {
  return (
    <p className="text-sm leading-6 text-stone-700">
      <strong className="text-ink">{label}：</strong>
      {children || "暂无"}
    </p>
  );
}


function ExplanationEvidenceNote({ explanation }) {
  if (!explanation?.source_issue_field && !explanation?.source_evidence && !explanation?.linked_revision_task_rank) {
    return null;
  }

  return (
    <div className="mt-2 rounded-md border border-stone-200 bg-white p-3 text-xs leading-5 text-stone-600">
      <div className="mb-1 flex flex-wrap items-center gap-2">
        <span className="font-semibold text-ink">对应诊断依据</span>
        {explanation.linked_revision_task_rank && <Pill tone="ink">对应必改任务 #{explanation.linked_revision_task_rank}</Pill>}
      </div>
      {explanation.source_issue_field && <p><strong className="text-ink">解决的问题：</strong>{explanation.source_issue_field}</p>}
      {explanation.source_evidence && <p className="mt-1"><strong className="text-ink">原文证据：</strong>{explanation.source_evidence}</p>}
    </div>
  );
}


function toneForConfidence(confidence) {
  if (confidence === "high") return "low";
  if (confidence === "medium") return "medium";
  return "stone";
}


function fallbackTasksFromBlockers(blockers) {
  return asArray(blockers).slice(0, 3).map((item, index) => ({
    rank: item.rank || index + 1,
    title: item.issue || "处理核心阻碍",
    target_field: item.field,
    evidence: item.evidence,
    reason: item.why_it_blocks,
    expected_effect: "trust",
    suggested_action: item.suggested_focus,
    status: "todo",
  }));
}


function fallbackEvidenceFromIssues(issues) {
  return asArray(issues).map((item) => ({
    field: item.field,
    evidence: item.original_excerpt,
    judgement: item.issue,
    why_it_matters: item.why_it_matters,
    impact_area: item.impact_area,
    confidence: "medium",
    severity: item.severity,
    revision_principle: item.rewrite_principle,
    example_fix: item.example_fix,
    needs_user_input: false,
  }));
}


function DiagnosisSourcesBody({ sources }) {
  const list = asArray(sources);
  return (
    <>
      {list.length > 0 ? (
        <div className="grid gap-3 md:grid-cols-2">
          {list.map((item) => (
            <article key={item.field} className="rounded-lg border border-stone-200 bg-stone-50 p-4">
              <div className="mb-3 flex flex-wrap items-center gap-2">
                <h3 className="text-sm font-semibold text-ink">{item.field}</h3>
                <Pill tone={item.provided ? "low" : "medium"}>{item.provided ? "已提供" : "未提供"}</Pill>
                <Pill tone={toneForConfidence(item.confidence)}>置信度：{labelFrom(CONFIDENCE_LABELS, item.confidence)}</Pill>
              </div>
              <p className="text-sm leading-6 text-stone-700">{item.note || "暂无说明。"}</p>
            </article>
          ))}
        </div>
      ) : (
        <p className="rounded-md bg-stone-50 p-3 text-sm text-stone-500">暂无诊断依据数据。</p>
      )}
    </>
  );
}


function DiagnosisSources({ sources }) {
  return (
    <ResultCard title="诊断依据面板" icon={ClipboardList}>
      <DiagnosisSourcesBody sources={sources} />
    </ResultCard>
  );
}


function SummaryPanel({ result }) {
  const explanation = result.score_explanation || fallbackScoreExplanation(result.overall_score);
  return (
    <section className="rounded-lg bg-ink p-6 text-white shadow-sm">
      <div className="grid gap-5 lg:grid-cols-[1fr_220px] lg:items-end">
        <div className="min-w-0">
          <p className="text-sm text-stone-200">一句话结论</p>
          <h1 className="mt-2 text-xl font-semibold text-white">发布前内容诊断</h1>
          <p className="mt-3 max-w-3xl text-base leading-7 text-white">{result.summary || "当前结果缺少一句话结论，请先参考必改任务完成发布前复核。"}</p>
          <p className="mt-2 text-sm leading-6 text-stone-300">基于原文证据的优化建议，不承诺平台表现。</p>
        </div>
        <div className="rounded-lg bg-white/10 p-4">
          <p className="text-sm text-stone-200">总分</p>
          <div className="mt-1 flex items-end gap-2">
            <p className="text-5xl font-bold leading-none">{result.overall_score ?? "--"}</p>
            <span className="pb-1 text-sm text-stone-200">/100</span>
          </div>
          <div className="mt-3 flex flex-wrap items-center gap-2">
            <Pill tone={scoreBand(result.overall_score).tone}>{explanation.band}</Pill>
          </div>
          <p className="mt-2 text-xs leading-5 text-stone-200">{explanation.interpretation}</p>
          {asArray(explanation.main_loss_factors).length > 0 && (
            <div className="mt-3 border-t border-white/10 pt-3">
              <p className="text-xs font-semibold text-stone-200">主要失分因素</p>
              <ul className="mt-2 space-y-1 text-xs leading-5 text-stone-200">
                {asArray(explanation.main_loss_factors).map((item, index) => (
                  <li key={`${item}-${index}`}>- {item}</li>
                ))}
              </ul>
            </div>
          )}
          <p className="mt-3 text-xs leading-5 text-stone-200">{explanation.next_score_goal}</p>
          <p className="mt-2 text-xs leading-5 text-stone-300">{explanation.disclaimer}</p>
        </div>
      </div>
      <div className="mt-4 flex flex-wrap gap-2">
        {result.category && <span className="rounded-full bg-white/10 px-3 py-1 text-xs font-semibold text-stone-100">{result.category}</span>}
        {result.diagnosis_id && <span className="rounded-full bg-white/10 px-3 py-1 text-xs font-semibold text-stone-100">ID {result.diagnosis_id.slice(0, 8)}</span>}
      </div>
    </section>
  );
}


function RevisionTasks({ tasks, fallbackBlockers }) {
  const primaryTasks = asArray(tasks);
  const list = primaryTasks.length > 0 ? primaryTasks : fallbackTasksFromBlockers(fallbackBlockers);
  return (
    <ResultCard title="Top 3 必改任务" icon={AlertTriangle}>
      {list.length > 0 ? (
        <div className="grid gap-3 lg:grid-cols-3">
          {list.map((item) => (
            <article key={`${item.rank}-${item.target_field}`} className="rounded-lg border border-stone-200 bg-stone-50 p-4">
              <div className="mb-3 flex flex-wrap items-center gap-2">
                <Pill tone="ink">#{item.rank}</Pill>
                <Pill>{labelFrom(IMPACT_LABELS, item.expected_effect)}</Pill>
                <span className="text-xs font-semibold text-stone-500">{item.status || "todo"}</span>
              </div>
              <h3 className="text-sm font-semibold text-ink">{item.title}</h3>
              <div className="mt-3 space-y-2">
                <FieldLine label="目标字段">{item.target_field}</FieldLine>
                <FieldLine label="原文证据">{item.evidence}</FieldLine>
                <FieldLine label="为什么要改">{item.reason}</FieldLine>
                <FieldLine label="影响指标">{labelFrom(IMPACT_LABELS, item.expected_effect)}</FieldLine>
                <FieldLine label="建议动作">{item.suggested_action}</FieldLine>
              </div>
            </article>
          ))}
        </div>
      ) : (
        <p className="rounded-md bg-stone-50 p-3 text-sm text-stone-500">暂无必改任务，发布前仍建议人工复核关键证据和风险表达。</p>
      )}
    </ResultCard>
  );
}


function ScoreDeductionsBody({ result }) {
  const deductions = asArray(result.score_deductions);
  const scores = asArray(result.scores);
  return (
    <>
      <div className="mb-4 rounded-lg bg-stone-50 p-4">
        <p className="text-xs font-semibold text-stone-500">总分</p>
        <p className="mt-1 text-5xl font-bold text-ink">{result.overall_score}</p>
        <p className="mt-2 text-sm leading-6 text-stone-600">分数来自规则诊断，真实 AI 只做自然语言增强和改写。</p>
      </div>

      {deductions.length > 0 ? (
        <div className="space-y-3">
          {deductions.map((item, index) => (
            <article key={`${item.dimension}-${index}`} className="rounded-lg border border-stone-200 bg-stone-50 p-4">
              <div className="mb-3 flex flex-wrap items-center gap-2">
                <h3 className="text-sm font-semibold text-ink">{item.dimension}</h3>
                <Pill tone="medium">扣 {item.points_lost} 分</Pill>
              </div>
              <div className="space-y-2">
                <FieldLine label="原文证据">{item.evidence}</FieldLine>
                <FieldLine label="扣分原因">{item.reason}</FieldLine>
                <FieldLine label="提升路径">{item.improvement_path}</FieldLine>
              </div>
            </article>
          ))}
        </div>
      ) : (
        <div>
          <p className="mb-3 rounded-md bg-stone-50 p-3 text-sm text-stone-500">暂无明确扣分解释，以下保留原评分分项。</p>
          <div className="grid gap-3 md:grid-cols-2">
            {scores.map((item) => (
              <ScoreBar key={item.key || item.name} item={item} />
            ))}
          </div>
        </div>
      )}
    </>
  );
}


function ScoreDeductions({ result }) {
  return (
    <ResultCard title="总分与扣分解释" icon={Sparkles}>
      <ScoreDeductionsBody result={result} />
    </ResultCard>
  );
}


function ReaderPerspectivesBody({ perspectives }) {
  const list = asArray(perspectives);
  return (
    <>
      {list.length > 0 ? (
        <div className="space-y-3">
          {list.map((item) => (
            <article key={item.stage} className="rounded-lg border border-stone-200 bg-stone-50 p-4">
              <div className="mb-3 flex flex-wrap items-center gap-2">
                <Pill tone="ink">{labelFrom(STAGE_LABELS, item.stage)}</Pill>
                <span className="text-xs font-semibold text-stone-500">读者路径</span>
              </div>
              <div className="space-y-2">
                <FieldLine label="读者可能反应">{item.likely_reaction}</FieldLine>
                <FieldLine label="信任变化">{item.trust_change}</FieldLine>
                <FieldLine label="行动意愿">{item.action_intent}</FieldLine>
                <FieldLine label="原文证据">{item.evidence}</FieldLine>
              </div>
            </article>
          ))}
        </div>
      ) : (
        <p className="rounded-md bg-stone-50 p-3 text-sm text-stone-500">暂无读者视角模拟。</p>
      )}
    </>
  );
}


function ReaderPerspectives({ perspectives }) {
  return (
    <ResultCard title="读者视角模拟" icon={UserRound}>
      <ReaderPerspectivesBody perspectives={perspectives} />
    </ResultCard>
  );
}


function EvidenceDiagnosisBody({ items, fallbackIssues }) {
  const primaryItems = asArray(items);
  const list = primaryItems.length > 0 ? primaryItems : fallbackEvidenceFromIssues(fallbackIssues);
  return (
    <>
      {list.length > 0 ? (
        <div className="space-y-3">
          {list.map((item, index) => (
            <article key={`${item.field}-${index}`} className="rounded-lg border border-stone-200 bg-stone-50 p-4">
              <div className="mb-3 flex flex-wrap items-center gap-2">
                <Pill tone={item.severity}>{labelFrom(SEVERITY_LABELS, item.severity)}</Pill>
                <Pill>{labelFrom(IMPACT_LABELS, item.impact_area)}</Pill>
                <Pill tone={toneForConfidence(item.confidence)}>置信度：{labelFrom(CONFIDENCE_LABELS, item.confidence)}</Pill>
                <span className="text-xs font-semibold text-stone-500">{item.field}</span>
              </div>
              <div className="space-y-2">
                <FieldLine label="原文证据">{item.evidence}</FieldLine>
                <FieldLine label="明确判断">{item.judgement}</FieldLine>
                <FieldLine label="为什么重要">{item.why_it_matters}</FieldLine>
                <FieldLine label="修改原则">{item.revision_principle}</FieldLine>
                <FieldLine label="示例改法">{item.example_fix}</FieldLine>
                <FieldLine label="是否需要补充用户信息">{item.needs_user_input ? "需要" : "不需要"}</FieldLine>
              </div>
            </article>
          ))}
        </div>
      ) : (
        <p className="rounded-md bg-stone-50 p-3 text-sm text-stone-500">暂无证据型问题诊断。</p>
      )}
    </>
  );
}


function EvidenceDiagnosis({ items, fallbackIssues }) {
  return (
    <ResultCard title="证据型问题诊断 / 逐条证据诊断" icon={ClipboardList}>
      <EvidenceDiagnosisBody items={items} fallbackIssues={fallbackIssues} />
    </ResultCard>
  );
}


function SimilarCasesBody({ result }) {
  const samples = asArray(result.matched_samples);
  const insights = result.sample_insights || {};
  return (
    <>
      {result.case_match_message && <p className="mb-3 text-sm leading-6 text-stone-600">{result.case_match_message}</p>}
      <div className="mb-4 rounded-lg border border-stone-200 bg-stone-50 p-4">
        <div className="mb-3 flex flex-wrap items-center gap-2">
          <Pill tone="ink">样本数量：{insights.sample_count ?? samples.length}</Pill>
          <span className="text-xs font-semibold text-stone-500">只做结构参考</span>
        </div>
        <div className="grid gap-4 lg:grid-cols-3">
          <div>
            <h3 className="mb-2 text-sm font-semibold text-ink">可复用标题结构</h3>
            <TextList items={insights.title_patterns} emptyText="暂无可复用标题结构。" />
          </div>
          <div>
            <h3 className="mb-2 text-sm font-semibold text-ink">可复用开头结构</h3>
            <TextList items={insights.opening_patterns} emptyText="暂无可复用开头结构。" />
          </div>
          <div>
            <h3 className="mb-2 text-sm font-semibold text-ink">可信信号</h3>
            <TextList items={insights.trust_signals} emptyText="暂无可信信号参考。" />
          </div>
        </div>
        <div className="mt-4">
          <h3 className="mb-2 text-sm font-semibold text-ink">可复用内容结构</h3>
          <TextList items={insights.reusable_structures} emptyText="暂无可复用内容结构。" />
        </div>
        <p className="mt-4 rounded-md bg-white p-3 text-sm leading-6 text-stone-600">{insights.caution || "样本仅供结构参考，不代表平台表现。"}</p>
      </div>
      {samples.length > 0 ? (
        <div className="space-y-3">
          {samples.map((sample, index) => (
            <article key={`${sample.title}-${index}`} className="rounded-lg border border-stone-200 bg-stone-50 p-4">
              <h3 className="text-sm font-semibold text-ink">{sample.title || `案例 ${index + 1}`}</h3>
              <p className="mt-2 text-sm leading-6 text-stone-700">{sample.similarity_reason || sample.content || "暂无案例说明。"}</p>
              {sample.caution && <p className="mt-2 text-xs leading-5 text-stone-500">{sample.caution}</p>}
            </article>
          ))}
        </div>
      ) : (
        <p className="rounded-md bg-stone-50 p-3 text-sm text-stone-500">暂无相似案例；系统不会抓取平台内容，只使用用户自有或授权样本。</p>
      )}
    </>
  );
}


function SimilarCases({ result }) {
  return (
    <ResultCard title="授权样本结构参考" icon={Layers3}>
      <SimilarCasesBody result={result} />
    </ResultCard>
  );
}


function LoadingState() {
  return (
    <section className="flex min-h-[520px] items-center justify-center rounded-lg border border-stone-200 bg-white p-8 text-center shadow-sm">
      <div>
        <Sparkles className="mx-auto h-8 w-8 animate-pulse text-rosewood" />
        <h2 className="mt-4 text-lg font-semibold text-ink">正在生成发布前内容诊断</h2>
        <p className="mt-2 text-sm text-stone-500">正在检查诊断依据、原文证据、必改任务、改写理由和风险表达。</p>
      </div>
    </section>
  );
}


function EmptyState() {
  return (
    <section className="flex min-h-[520px] items-center justify-center rounded-lg border border-dashed border-stone-300 bg-white p-8 text-center">
      <div>
        <FileText className="mx-auto h-9 w-9 text-stone-400" />
        <h2 className="mt-4 text-lg font-semibold text-ink">小红书发布前证据型诊断工作台</h2>
        <p className="mt-2 max-w-md text-sm leading-6 text-stone-500">
          填写左侧内容后，这里会展示基于原文证据的优化建议、读者视角、改写版本和合规风险；不承诺平台表现。
        </p>
      </div>
    </section>
  );
}


function RewrittenVersions({ result, onCopy }) {
  const versions = result.rewritten_versions || {};
  const titles = asArray(versions.titles?.length ? versions.titles : result.rewritten_titles);
  const body = versions.body || result.optimized_body || "";
  const tags = asArray(versions.tags?.length ? versions.tags : result.recommended_tags);
  const covers = asArray(versions.cover_text?.length ? versions.cover_text : result.cover_text);
  const comments = asArray(versions.comment_guides?.length ? versions.comment_guides : result.comment_guides);
  const explanations = asArray(result.rewrite_explanations);
  const explanationByTarget = new Map(explanations.map((item) => [item.target, item]));
  const tagExplanation = explanationByTarget.get("标签");

  return (
    <ResultCard title="可复制改写版本" icon={FileText}>
      <div className="space-y-4">
        <div>
          <div className="mb-2 flex items-center justify-between gap-2">
            <h3 className="text-sm font-semibold text-ink">标题</h3>
            {titles.length > 0 && <CopyMiniButton text={titles.join("\n")} label="复制标题" onCopy={onCopy} />}
          </div>
          {titles.length > 0 ? (
            <div className="grid gap-2">
              {titles.map((title, index) => (
                <div key={`${title}-${index}`} className="rounded-md bg-stone-50 px-3 py-2">
                  <div className="flex items-center justify-between gap-3 text-sm font-medium text-ink">
                    <span>{index + 1}. {title}</span>
                    <CopyMiniButton text={title} onCopy={onCopy} />
                  </div>
                  <ExplanationEvidenceNote explanation={explanationByTarget.get(`标题${index + 1}`)} />
                </div>
              ))}
            </div>
          ) : (
            <p className="rounded-md bg-amber-50 p-3 text-sm leading-6 text-amber-800">当前内容存在高风险，系统已暂停生成营销化标题。</p>
          )}
        </div>

        <div>
          <div className="mb-2 flex items-center justify-between gap-2">
            <h3 className="text-sm font-semibold text-ink">正文结构</h3>
            {body && <CopyMiniButton text={body} label="复制正文" onCopy={onCopy} />}
          </div>
          <p className="whitespace-pre-line rounded-md bg-stone-50 p-4 text-sm leading-7 text-stone-700">{body || "暂无正文改写。"}</p>
          <ExplanationEvidenceNote explanation={explanationByTarget.get("正文")} />
        </div>

        <div className="grid gap-4 xl:grid-cols-3">
          <div>
            <h3 className="mb-2 text-sm font-semibold text-ink">标签</h3>
            <div className="flex flex-wrap gap-2">
              {tags.map((tag) => (
                <span key={tag} className="rounded-full bg-rosewood/10 px-3 py-1 text-xs font-semibold text-rosewood">#{tag}</span>
              ))}
            </div>
            <ExplanationEvidenceNote explanation={tagExplanation} />
          </div>
          <div>
            <h3 className="mb-2 text-sm font-semibold text-ink">封面文案</h3>
            <div className="grid gap-2">
              {covers.map((item) => (
                <p key={item} className="rounded-md bg-stone-50 p-2 text-sm font-medium text-ink">{item}</p>
              ))}
            </div>
          </div>
          <div>
            <h3 className="mb-2 text-sm font-semibold text-ink">评论引导</h3>
            <div className="grid gap-2">
              {comments.map((item) => (
                <p key={item} className="rounded-md bg-stone-50 p-2 text-sm leading-6 text-stone-700">{item}</p>
              ))}
            </div>
          </div>
        </div>
      </div>
    </ResultCard>
  );
}


function RiskReviewBody({ result }) {
  const riskReview = result.risk_review || {};
  const riskItems = asArray(riskReview.risk_items);
  const safeAlternatives = asArray(riskReview.safe_alternatives);
  const legacyRisks = asArray(result.risks);

  return (
    <>
      <div className="mb-4 flex flex-wrap items-center gap-2">
        <Pill tone={riskReview.risk_level || riskReview.overall_level || "low"}>风险等级：{labelFrom(SEVERITY_LABELS, riskReview.risk_level || riskReview.overall_level || "low")}</Pill>
        {riskReview.human_review_required && <Pill tone="high">需要人工复核</Pill>}
      </div>

      {riskItems.length > 0 ? (
        <div className="space-y-3">
          {riskItems.map((item, index) => (
            <article key={`${item.field}-${item.triggered_text}-${index}`} className="rounded-lg border border-stone-200 bg-stone-50 p-4">
              <div className="mb-2 flex flex-wrap items-center gap-2">
                <Pill tone={item.severity}>{labelFrom(SEVERITY_LABELS, item.severity)}</Pill>
                <Pill>{item.risk_type}</Pill>
                <span className="text-xs font-semibold text-stone-500">{item.field}</span>
              </div>
              <p className="text-sm leading-6 text-stone-700"><strong className="text-ink">触发文本：</strong>{item.triggered_text}</p>
              <p className="mt-2 text-sm leading-6 text-stone-700"><strong className="text-ink">原因：</strong>{item.reason}</p>
              <p className="mt-2 text-sm leading-6 text-stone-700"><strong className="text-ink">保守改法：</strong>{item.suggested_rewrite}</p>
            </article>
          ))}
        </div>
      ) : (
        <TextList items={legacyRisks.map((risk) => `${risk.level}：${risk.message}`)} emptyText="未发现明显高风险表达，发布前仍建议人工复核。" />
      )}

      {safeAlternatives.length > 0 && (
        <div className="mt-4 rounded-lg bg-amber-50 p-4">
          <h3 className="text-sm font-semibold text-amber-900">安全替代表达</h3>
          <ul className="mt-2 space-y-2 text-sm leading-6 text-amber-800">
            {safeAlternatives.map((item) => (
              <li key={item}>- {item}</li>
            ))}
          </ul>
        </div>
      )}
    </>
  );
}


function RiskReview({ result }) {
  return (
    <ResultCard title="合规风险审查" icon={ShieldAlert}>
      <RiskReviewBody result={result} />
    </ResultCard>
  );
}


function MissingInputsBody({ missingInputs, answers, onAnswerChange, onRefine, refining }) {
  const answeredItems = missingInputs
    .map((item) => ({
      field: item.field,
      answer: (answers[item.field] || "").trim(),
    }))
    .filter((item) => item.answer);
  const canRefine = answeredItems.length > 0 && !refining && Boolean(onRefine);

  return missingInputs.length > 0 ? (
    <div className="space-y-4">
      <div className="grid gap-3 md:grid-cols-2">
        {missingInputs.map((item) => (
          <article key={`${item.field}-${item.reason}`} className="rounded-lg bg-stone-50 p-4">
            <FieldLine label="缺失字段">{item.field}</FieldLine>
            <FieldLine label="原因">{item.reason}</FieldLine>
            <FieldLine label="建议补充问题">{item.suggested_prompt}</FieldLine>
            <label className="mt-3 block text-xs font-semibold text-stone-500" htmlFor={`missing-answer-${item.field}`}>
              用户补充信息
            </label>
            <textarea
              id={`missing-answer-${item.field}`}
              value={answers[item.field] || ""}
              onChange={(event) => onAnswerChange(item.field, event.target.value)}
              rows={3}
              className="mt-2 w-full resize-y rounded-md border border-stone-200 bg-white px-3 py-2 text-sm leading-6 text-ink outline-none focus:border-rosewood"
              placeholder="只填写你真实经历、观察或可公开信息；没有就留空。"
            />
          </article>
        ))}
      </div>
      <div className="flex flex-col gap-2 rounded-lg border border-stone-200 bg-white p-4 sm:flex-row sm:items-center sm:justify-between">
        <p className="text-sm leading-6 text-stone-600">系统会把已填写内容标注为“用户补充信息”后重新诊断，不会补写你没有提供的事实。</p>
        <button
          type="button"
          onClick={() => onRefine(answeredItems)}
          disabled={!canRefine}
          className="inline-flex shrink-0 items-center justify-center rounded-md bg-ink px-4 py-2 text-sm font-semibold text-white disabled:cursor-not-allowed disabled:bg-stone-300"
        >
          {refining ? "重新诊断中..." : "用补充信息重新诊断"}
        </button>
      </div>
    </div>
  ) : (
    <p className="rounded-md bg-stone-50 p-3 text-sm text-stone-500">当前输入已包含基础可信细节，仍建议发布前人工复核。</p>
  );
}


function StructureAnalysisBody({ structure }) {
  return (
    <KeyValueGrid
      items={[
        ["开头 3 秒", structure.opening_hook],
        ["信息层次", structure.information_hierarchy],
        ["信任建立", structure.trust_building],
        ["细节证据", structure.detail_evidence],
        ["情绪共鸣", structure.emotional_resonance],
        ["行动引导", structure.action_guidance],
      ]}
    />
  );
}


function CredibilityReviewBody({ credibility }) {
  return (
    <>
      <div className="mb-3 flex flex-wrap gap-2">
        <Pill tone={credibility.is_too_generic ? "medium" : "low"}>{credibility.is_too_generic ? "表达偏泛" : "具体度尚可"}</Pill>
        <Pill tone={credibility.sounds_like_ad ? "medium" : "low"}>{credibility.sounds_like_ad ? "广告感偏强" : "广告感可控"}</Pill>
      </div>
      <div className="grid gap-4 md:grid-cols-2">
        <div>
          <h3 className="mb-2 text-sm font-semibold text-ink">缺失信任信号</h3>
          <TextList items={credibility.missing_trust_signals} emptyText="暂无明显缺失。" />
        </div>
        <div>
          <h3 className="mb-2 text-sm font-semibold text-ink">已有信任信号</h3>
          <TextList items={credibility.strong_trust_signals} emptyText="暂无明显信任信号。" />
        </div>
      </div>
    </>
  );
}


function RewriteExplanationsBody({ explanations }) {
  if (explanations.length === 0) {
    return <p className="rounded-md bg-stone-50 p-3 text-sm text-stone-500">暂无改写理由。</p>;
  }

  return (
    <div className="space-y-3">
      {explanations.map((item, index) => (
        <article key={`${item.target}-${index}`} className="rounded-lg border border-stone-200 bg-stone-50 p-4">
          <div className="mb-2 flex flex-wrap items-center gap-2">
            <Pill tone="ink">{item.target}</Pill>
            <Pill>{labelFrom(IMPACT_LABELS, item.expected_effect)}</Pill>
            {item.linked_revision_task_rank && <Pill tone="medium">对应必改任务 #{item.linked_revision_task_rank}</Pill>}
          </div>
          <p className="text-sm leading-6 text-stone-700"><strong className="text-ink">解决的问题：</strong>{item.source_issue_field || "未绑定具体诊断问题"}</p>
          <p className="mt-2 text-sm leading-6 text-stone-700"><strong className="text-ink">原文证据：</strong>{item.source_evidence || item.original_excerpt}</p>
          <p className="text-sm leading-6 text-stone-700"><strong className="text-ink">原文：</strong>{item.original_excerpt}</p>
          <p className="mt-2 text-sm leading-6 text-stone-700"><strong className="text-ink">改写：</strong>{item.rewritten_excerpt}</p>
          <p className="mt-2 text-sm leading-6 text-stone-700"><strong className="text-ink">说明：</strong>{item.reason}</p>
          <p className="mt-2 text-sm leading-6 text-stone-700"><strong className="text-ink">预期改善指标：</strong>{labelFrom(IMPACT_LABELS, item.expected_effect)}</p>
        </article>
      ))}
    </div>
  );
}


export function DiagnosisResult({ result, loading, refineLoading = false, onRefine }) {
  const [copyMessage, setCopyMessage] = useState("");
  const [missingAnswers, setMissingAnswers] = useState({});

  function showCopyMessage(message) {
    setCopyMessage(message);
    window.setTimeout(() => setCopyMessage(""), 2200);
  }

  function updateMissingAnswer(field, value) {
    setMissingAnswers((current) => ({ ...current, [field]: value }));
  }

  function handleRefine(answers) {
    onRefine?.(answers);
  }

  useEffect(() => {
    setMissingAnswers({});
  }, [result?.diagnosis_id]);

  if (loading) return <LoadingState />;
  if (!result) return <EmptyState />;

  const structure = result.structure_analysis || {};
  const credibility = result.credibility_review || {};
  const missingInputs = asArray(result.missing_user_inputs);
  const explanations = asArray(result.rewrite_explanations);

  return (
    <div className="space-y-4">
      {copyMessage && (
        <div className="rounded-md border border-mint/20 bg-mint/10 px-3 py-2 text-sm font-semibold text-mint">
          {copyMessage}
        </div>
      )}

      <SummaryPanel result={result} />

      <RevisionTasks tasks={result.revision_tasks} fallbackBlockers={result.top_3_blockers} />

      <RewrittenVersions result={result} onCopy={showCopyMessage} />

      <AccordionSection title="诊断依据面板" icon={ClipboardList}>
        <DiagnosisSourcesBody sources={result.diagnosis_sources} />
      </AccordionSection>

      <AccordionSection title="总分与扣分解释" icon={Sparkles}>
        <ScoreDeductionsBody result={result} />
      </AccordionSection>

      <AccordionSection title="读者视角模拟" icon={UserRound}>
        <ReaderPerspectivesBody perspectives={result.reader_perspectives} />
      </AccordionSection>

      <AccordionSection title="证据型问题诊断" icon={ClipboardList}>
        <EvidenceDiagnosisBody items={result.evidence_diagnosis} fallbackIssues={result.evidence_based_issues} />
      </AccordionSection>

      <AccordionSection title="内容结构分析" icon={Layers3}>
        <StructureAnalysisBody structure={structure} />
      </AccordionSection>

      <AccordionSection title="可信度检查" icon={Eye}>
        <CredibilityReviewBody credibility={credibility} />
      </AccordionSection>

      <AccordionSection title="改写理由" icon={Info}>
        <RewriteExplanationsBody explanations={explanations} />
      </AccordionSection>

      <AccordionSection title="授权样本结构参考" icon={Layers3}>
        <SimilarCasesBody result={result} />
      </AccordionSection>

      <AccordionSection title="缺失信息补充" icon={HelpCircle}>
        <MissingInputsBody
          missingInputs={missingInputs}
          answers={missingAnswers}
          onAnswerChange={updateMissingAnswer}
          onRefine={handleRefine}
          refining={refineLoading}
        />
      </AccordionSection>

      <AccordionSection title="合规风险审查" icon={ShieldAlert}>
        <RiskReviewBody result={result} />
      </AccordionSection>

      {result.ai_disclosure_notice && (
        <section className="rounded-lg border border-stone-200 bg-stone-50 p-4 text-sm leading-6 text-stone-600">
          <div className="flex gap-2">
            <Info className="mt-1 h-4 w-4 shrink-0 text-stone-500" />
            <p>{result.ai_disclosure_notice}</p>
          </div>
        </section>
      )}
    </div>
  );
}
