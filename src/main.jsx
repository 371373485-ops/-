import React, { useMemo, useState } from 'react';
import { createRoot } from 'react-dom/client';
import {
  AlertCircle,
  BarChart3,
  CheckCircle2,
  ClipboardList,
  Hash,
  Lightbulb,
  MessageCircle,
  PenLine,
  RefreshCw,
  Sparkles,
  Target,
} from 'lucide-react';
import './styles.css';

const defaultForm = {
  niche: '职场成长 / 副业变现',
  audience: '25-35 岁的一线/新一线城市职场女性，想提升收入但时间有限',
  title: '普通人做副业，如何从0开始赚钱？',
  body:
    '很多人都想做副业，但不知道从哪里开始。我之前也试过很多方法，踩过不少坑。后来发现，普通人最重要的是先找到自己已有的能力，再选择一个小切口持续输出。\n\n第一步，盘点你能解决什么问题。第二步，找到愿意为这个问题付费的人。第三步，把经验整理成可复制的内容。不要一开始就追求完美，先做起来，再根据反馈优化。',
  tags: '副业, 职场成长, 普通人赚钱, 个人成长',
};

const dimensionMeta = [
  { key: 'title', label: '标题吸引力', icon: PenLine },
  { key: 'hook', label: '开头留存', icon: Sparkles },
  { key: 'structure', label: '内容结构', icon: ClipboardList },
  { key: 'emotion', label: '情绪共鸣', icon: MessageCircle },
  { key: 'value', label: '信息价值', icon: Lightbulb },
  { key: 'interaction', label: '互动设计', icon: CheckCircle2 },
  { key: 'tag', label: '标签匹配', icon: Hash },
];

const genericWords = new Set([
  '内容',
  '分享',
  '干货',
  '方法',
  '建议',
  '问题',
  '经验',
  '笔记',
  '普通人',
  '新手',
]);

function clamp(value, min = 0, max = 100) {
  return Math.max(min, Math.min(max, Math.round(value)));
}

function countMatches(text, patterns) {
  return patterns.reduce((sum, pattern) => sum + (pattern.test(text) ? 1 : 0), 0);
}

function splitTags(tags) {
  return tags
    .split(/[,，#\s]+/)
    .map((tag) => tag.trim())
    .filter(Boolean);
}

function splitClauses(text) {
  return text
    .split(/[。！？!?；;\n]+/)
    .map((item) => item.trim())
    .filter(Boolean);
}

function compact(text, max = 34) {
  const clean = text.replace(/\s+/g, '');
  return clean.length > max ? `${clean.slice(0, max)}...` : clean;
}

function firstUseful(items, fallback) {
  return items.find((item) => item && item.trim())?.trim() || fallback;
}

function extractContext(form, tags) {
  const title = form.title.trim();
  const body = form.body.trim();
  const clauses = splitClauses(body);
  const nicheParts = form.niche.split(/[\/,，、|｜]+/).map((item) => item.trim()).filter(Boolean);
  const audienceParts = form.audience.split(/[，,。；;]+/).map((item) => item.trim()).filter(Boolean);
  const allText = `${form.niche} ${form.audience} ${title} ${body} ${tags.join(' ')}`;

  const topic =
    [...tags, ...nicheParts, ...title.match(/[\u4e00-\u9fa5A-Za-z0-9]{2,10}/g) || []].find(
      (word) => word.length >= 2 && !genericWords.has(word),
    ) || '当前主题';
  const audience = firstUseful(audienceParts, '目标人群');
  const pain =
    clauses.find((line) => /不知道|不会|没|没有|很难|焦虑|迷茫|踩坑|怕|卡|问题|痛点|时间有限|太/.test(line)) ||
    title;
  const method =
    clauses.find((line) => /第一|第二|第三|步骤|方法|可以|建议|先|再|最后|核心|关键|不要/.test(line)) ||
    clauses[0] ||
    title;
  const proof =
    clauses.find((line) => /我|之前|后来|亲测|真实|复盘|踩过|发现|结果/.test(line)) || '';
  const outcome =
    allText.match(/提升收入|赚钱|涨粉|转化|变现|省钱|变美|减脂|成长|提高效率|避坑|拿到结果|持续输出/)?.[0] ||
    '拿到结果';
  const titleKeyword =
    title.match(/[\u4e00-\u9fa5A-Za-z0-9]{2,10}/g)?.find((word) => !genericWords.has(word)) || topic;

  return { topic, audience, pain, method, proof, outcome, titleKeyword, clauses, nicheParts, allText };
}

function buildDimensionResult(score, strongText, weakText) {
  return score >= 80 ? strongText : weakText;
}

function diagnose(form) {
  const title = form.title.trim();
  const body = form.body.trim();
  const tags = splitTags(form.tags);
  const ctx = extractContext(form, tags);
  const firstParagraph = body.split(/\n+/)[0] || '';
  const paragraphs = body.split(/\n+/).filter(Boolean);
  const bodyLength = body.replace(/\s/g, '').length;
  const titleLength = title.replace(/\s/g, '').length;

  const titleSignals = countMatches(title, [
    /\d/,
    /普通人|新手|小白|上班族|宝妈|学生|打工人|妈妈|女生|男生/,
    /如何|怎么|为什么|避坑|清单|方法|模板|复盘|攻略|指南/,
    /0到1|从0|一周|三天|月入|提升|变好|搞定|赚钱|变现|涨粉/,
    /[？?！!]/,
  ]);
  const titleScore = clamp(50 + titleSignals * 9 + (titleLength >= 12 && titleLength <= 30 ? 12 : -8));

  const hookSignals = countMatches(firstParagraph, [
    /你是不是|有没有|很多人|普通人|我发现|说真的/,
    /痛点|焦虑|迷茫|踩坑|后悔|误区|问题|不知道|不会/,
    /结果|后来|终于|亲测|真实|之前/,
    /\d/,
  ]);
  const hookScore = clamp(48 + hookSignals * 11 + (firstParagraph.length <= 110 ? 8 : -5));

  const structureSignals =
    paragraphs.length +
    countMatches(body, [/第一|第二|第三|步骤|方法|清单|总结|避坑|案例|原因|结论|1[\.、]|2[\.、]|3[\.、]/]) * 2;
  const structureScore = clamp(45 + structureSignals * 6 + (bodyLength >= 220 ? 8 : -8));

  const emotionSignals = countMatches(body, [
    /我|自己|亲身|真实|以前|之前|后来/,
    /焦虑|迷茫|害怕|开心|惊喜|后悔|松了一口气|累|崩溃/,
    /普通人|打工人|姐妹|你|我们/,
    /踩坑|坚持|改变|不甘心/,
  ]);
  const emotionScore = clamp(44 + emotionSignals * 9);

  const valueSignals = countMatches(body, [
    /方法|步骤|模板|清单|案例|复盘|工具|公式|建议|标准/,
    /第一|第二|第三|\d+[\.、]/,
    /具体|可复制|执行|反馈|优化|落地|盘点|整理/,
    /不要|一定|优先|核心|关键/,
  ]);
  const valueScore = clamp(42 + valueSignals * 10 + (bodyLength >= 280 ? 8 : -4));

  const interactionSignals = countMatches(body, [
    /评论|收藏|点赞|关注|私信|留言/,
    /你会|你想|你觉得|你最|一起|哪一步|哪里/,
    /告诉我|发给你|整理好了/,
  ]);
  const interactionScore = clamp(36 + interactionSignals * 16);

  const tagCoverage = tags.length >= 5 ? 18 : tags.length * 3;
  const tagRelevance = tags.filter((tag) => ctx.allText.includes(tag)).length * 5;
  const tagScore = clamp(42 + tagCoverage + tagRelevance + (tags.length > 8 ? -8 : 0));

  const scores = {
    title: titleScore,
    hook: hookScore,
    structure: structureScore,
    emotion: emotionScore,
    value: valueScore,
    interaction: interactionScore,
    tag: tagScore,
  };

  const diagnostics = {
    title: buildDimensionResult(
      titleScore,
      `标题已经围绕「${ctx.titleKeyword}」建立了点击点，可以继续强化结果承诺。`,
      `当前标题「${compact(title)}」提到了主题，但没有把「${compact(ctx.audience, 18)}」和「${ctx.outcome}」说得足够具体。`,
    ),
    hook: buildDimensionResult(
      hookScore,
      `开头能抓住「${compact(ctx.pain)}」这个真实问题，有继续阅读的理由。`,
      `开头还可以更直接。建议第一句话就点出「${compact(ctx.pain)}」，不要先做泛泛背景铺垫。`,
    ),
    structure: buildDimensionResult(
      structureScore,
      `正文已经有步骤感，尤其是「${compact(ctx.method)}」这一段适合拆成小标题。`,
      `正文结构还不够利于扫读。可以把「${compact(ctx.method)}」拆成 3 个明确动作，并补一个结果收束。`,
    ),
    emotion: buildDimensionResult(
      emotionScore,
      `内容里有个人经历或代入感，能让「${compact(ctx.audience, 20)}」看到自己。`,
      `情绪共鸣偏弱。可以围绕「${compact(ctx.pain)}」补一句真实处境，比如为什么会急、怕什么、踩过什么坑。`,
    ),
    value: buildDimensionResult(
      valueScore,
      `信息价值比较明确，读者能从「${compact(ctx.method)}」里拿到可执行动作。`,
      `价值感需要再落细。建议把「${compact(ctx.method)}」补成判断标准、操作例子或可复制模板。`,
    ),
    interaction: buildDimensionResult(
      interactionScore,
      `结尾已有互动意识，可以继续把问题问得更具体。`,
      `互动设计不足。结尾可以问「你现在卡在${ctx.topic}的哪一步？」把评论入口和正文主题绑定。`,
    ),
    tag: buildDimensionResult(
      tagScore,
      `标签能覆盖「${ctx.topic}」和原始主题，平台识别方向较清楚。`,
      `标签还不够精准。当前应补充「${ctx.topic}」「${ctx.outcome}」「${compact(ctx.audience, 12)}」这类赛道、人群和结果词。`,
    ),
  };

  const total = clamp(
    scores.title * 0.16 +
      scores.hook * 0.15 +
      scores.structure * 0.14 +
      scores.emotion * 0.14 +
      scores.value * 0.17 +
      scores.interaction * 0.12 +
      scores.tag * 0.12,
  );

  const weakDimensions = dimensionMeta
    .filter(({ key }) => scores[key] < 72)
    .sort((a, b) => scores[a.key] - scores[b.key])
    .slice(0, 2)
    .map((item) => item.label);

  const summary =
    weakDimensions.length > 0
      ? `这篇笔记的主题是「${ctx.topic}」，主要短板在${weakDimensions.join('和')}。建议先让标题和前三行更明确地承接「${compact(ctx.pain)}」，再把正文方法拆成可收藏的步骤。`
      : `这篇笔记围绕「${ctx.topic}」的表达比较完整，接下来重点是把标题结果感和评论引导做得更锋利。`;

  const titleBase = ctx.topic === '当前主题' ? ctx.titleKeyword : ctx.topic;
  const optimizedTitles = [
    `${compact(ctx.audience, 18)}做${titleBase}，先避开这 3 个坑`,
    `我踩过坑才明白：${titleBase}真正有效的是这几步`,
    `${title}｜把「不知道从哪开始」改成可执行清单`,
  ];

  const recommendedTags = Array.from(
    new Set([
      titleBase,
      ctx.outcome,
      compact(ctx.audience, 12),
      ...ctx.nicheParts,
      ...tags,
      '小红书笔记',
      '干货分享',
      '新手必看',
    ]),
  )
    .filter((tag) => tag && tag.length <= 14)
    .slice(0, 9);

  const proofLine = ctx.proof
    ? `我自己最有感触的是：${ctx.proof}。这句话可以保留，因为它能证明你不是在空讲道理。`
    : `可以补一句真实经历：你为什么开始关注「${titleBase}」，中间踩过什么坑，最后发现了什么。`;

  const optimizedBody = [
    `如果你也在纠结「${compact(ctx.pain, 42)}」，这篇建议先收藏。`,
    proofLine,
    `我会把这篇笔记的核心改成一个更清楚的逻辑：先说明为什么卡住，再给出能马上执行的步骤。`,
    `1. 先锁定问题：围绕「${ctx.topic}」不要写太散，先回答读者最关心的「我为什么做不起来」。`,
    `2. 再拆已有方法：你原文里的「${compact(ctx.method, 45)}」可以拆成 3 个动作，每个动作配一个例子。`,
    `3. 最后给判断标准：做完以后怎么判断有效，比如是否能得到反馈、是否能持续输出、是否能靠近「${ctx.outcome}」。`,
    `可以直接照这个结构写：痛点开场 - 个人踩坑 - 3 个步骤 - 1 个避坑提醒 - 评论区提问。`,
    `你现在卡在「${titleBase}」的哪一步？是选方向、开始执行，还是坚持不下去？评论区告诉我，我可以继续拆。`,
  ].join('\n\n');

  const suggestions = [
    `标题建议从「${compact(title)}」改成“人群 + 痛点 + 结果”，比如突出「${compact(ctx.audience, 16)}」和「${ctx.outcome}」。`,
    `前三行不要只说主题，直接写「${compact(ctx.pain)}」，让读者马上判断“这说的是我”。`,
    `正文里「${compact(ctx.method)}」是最有价值的部分，建议拆成编号清单，每一点补一个具体例子。`,
    ctx.proof
      ? `保留「${compact(ctx.proof)}」这类真实经历，并补上当时的情绪或结果，增强信任感。`
      : `补一段真实经历，例如你为什么开始做「${ctx.topic}」、踩过什么坑、后来怎么调整。`,
    `结尾问题要和主题绑定：可以问“你现在卡在${titleBase}的哪一步？”而不是泛泛求评论。`,
    `标签增加「${titleBase}」「${ctx.outcome}」和人群词，减少过宽的泛标签。`,
  ];

  return {
    total,
    scores,
    diagnostics,
    suggestions,
    optimizedTitles,
    optimizedBody,
    recommendedTags,
    summary,
  };
}

function ScoreRing({ value }) {
  const angle = `${value * 3.6}deg`;
  return (
    <div className="score-ring" style={{ '--angle': angle }}>
      <div>
        <strong>{value}</strong>
        <span>爆款潜力</span>
      </div>
    </div>
  );
}

function App() {
  const [form, setForm] = useState(defaultForm);
  const [result, setResult] = useState(() => diagnose(defaultForm));
  const [hasRun, setHasRun] = useState(true);

  const readiness = useMemo(() => {
    const filled = Object.values(form).filter((value) => value.trim().length > 0).length;
    return Math.round((filled / 5) * 100);
  }, [form]);

  function updateField(field, value) {
    setForm((current) => ({ ...current, [field]: value }));
  }

  function runDiagnosis() {
    setResult(diagnose(form));
    setHasRun(true);
  }

  function resetDemo() {
    setForm(defaultForm);
    setResult(diagnose(defaultForm));
    setHasRun(true);
  }

  return (
    <main className="app-shell">
      <section className="workspace">
        <aside className="input-pane" aria-label="笔记输入区">
          <div className="brand-row">
            <div className="brand-mark">
              <Sparkles size={22} />
            </div>
            <div>
              <h1>小红书笔记爆款诊断 Agent</h1>
              <p>本地模拟评分，适合内容团队快速演示和改稿。</p>
            </div>
          </div>

          <div className="readiness">
            <span>输入完整度</span>
            <div className="meter" aria-hidden="true">
              <i style={{ width: `${readiness}%` }} />
            </div>
            <strong>{readiness}%</strong>
          </div>

          <label>
            <span>内容赛道</span>
            <input value={form.niche} onChange={(event) => updateField('niche', event.target.value)} />
          </label>
          <label>
            <span>目标人群</span>
            <input value={form.audience} onChange={(event) => updateField('audience', event.target.value)} />
          </label>
          <label>
            <span>笔记标题</span>
            <input value={form.title} onChange={(event) => updateField('title', event.target.value)} />
          </label>
          <label className="grow-field">
            <span>正文</span>
            <textarea value={form.body} onChange={(event) => updateField('body', event.target.value)} />
          </label>
          <label>
            <span>标签</span>
            <input value={form.tags} onChange={(event) => updateField('tags', event.target.value)} />
          </label>

          <div className="actions">
            <button className="primary-button" onClick={runDiagnosis}>
              <BarChart3 size={18} />
              开始诊断
            </button>
            <button className="ghost-button" onClick={resetDemo} title="恢复演示样例">
              <RefreshCw size={18} />
            </button>
          </div>
        </aside>

        <section className="result-pane" aria-label="诊断结果区">
          {!hasRun ? (
            <div className="empty-state">
              <Target size={42} />
              <p>填写左侧信息后开始诊断。</p>
            </div>
          ) : (
            <>
              <div className="result-hero">
                <ScoreRing value={result.total} />
                <div>
                  <p className="eyebrow">诊断结果</p>
                  <h2>{result.total >= 80 ? '具备爆款基础' : result.total >= 65 ? '有潜力，需强化关键钩子' : '需要重构选题表达'}</h2>
                  <p>{result.summary}</p>
                </div>
              </div>

              <div className="dimension-grid">
                {dimensionMeta.map(({ key, label, icon: Icon }) => (
                  <article className="dimension-card" key={key}>
                    <header>
                      <Icon size={18} />
                      <span>{label}</span>
                      <strong>{result.scores[key]}</strong>
                    </header>
                    <div className="mini-bar">
                      <i style={{ width: `${result.scores[key]}%` }} />
                    </div>
                    <p>{result.diagnostics[key]}</p>
                  </article>
                ))}
              </div>

              <section className="result-section">
                <h3>
                  <AlertCircle size={18} />
                  具体修改建议
                </h3>
                <ul className="suggestions">
                  {result.suggestions.map((item) => (
                    <li key={item}>{item}</li>
                  ))}
                </ul>
              </section>

              <section className="result-section split">
                <div>
                  <h3>
                    <PenLine size={18} />
                    3 个优化标题
                  </h3>
                  <div className="title-list">
                    {result.optimizedTitles.map((title) => (
                      <button key={title}>{title}</button>
                    ))}
                  </div>
                </div>
                <div>
                  <h3>
                    <Hash size={18} />
                    推荐标签
                  </h3>
                  <div className="tag-list">
                    {result.recommendedTags.map((tag) => (
                      <span key={tag}>#{tag}</span>
                    ))}
                  </div>
                </div>
              </section>

              <section className="result-section">
                <h3>
                  <ClipboardList size={18} />
                  优化后的正文
                </h3>
                <pre className="optimized-body">{result.optimizedBody}</pre>
              </section>
            </>
          )}
        </section>
      </section>
    </main>
  );
}

createRoot(document.getElementById('root')).render(<App />);
