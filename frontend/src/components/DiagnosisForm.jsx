import { AlertCircle, Loader2, Wand2 } from "lucide-react";


export const goalOptions = ["涨粉", "收藏", "引流", "转化", "种草"];

export const initialDiagnosisForm = {
  category: "护肤",
  target_audience: "刚开始认真护肤的新手",
  goal: "收藏",
  title: "新手护肤避坑清单！",
  content:
    "第一，我会先看成分和自己的肤质是否匹配。第二，我会记录真实体验，不会只看单次反馈。第三，我会把容易踩坑的地方整理出来，方便之后复盘和对比。",
  tags: "护肤,新手,经验分享",
  cover_text: "新手护肤先看这篇",
  comment_guide: "你现在最想解决哪一步？欢迎在评论区说说你的情况。",
};


function FieldLabel({ children, required = false }) {
  return (
    <span className="text-sm font-semibold text-ink">
      {children}
      {required && <span className="ml-1 text-rosewood">*</span>}
    </span>
  );
}


export function DiagnosisForm({ form, loading, error, diagnosisMode, onModeChange, onChange, onSubmit }) {
  return (
    <section className="rounded-lg border border-stone-200 bg-white p-5 shadow-sm">
      <div className="mb-5 flex items-start justify-between gap-4">
        <div>
          <h2 className="text-lg font-bold text-ink">发布前输入</h2>
          <p className="mt-1 text-sm leading-6 text-stone-500">粘贴准备发布的内容，系统只基于你提供的文本和授权样本诊断。</p>
        </div>
        <span className="rounded-full bg-mint/10 px-3 py-1 text-xs font-semibold text-mint">
          {diagnosisMode === "workflow" ? "多 Agent" : diagnosisMode === "ai" ? "AI" : "规则"}
        </span>
      </div>

      <form className="space-y-4" onSubmit={onSubmit}>
        <div>
          <FieldLabel>诊断模式</FieldLabel>
          <div className="mt-2 grid grid-cols-3 rounded-md border border-stone-300 bg-stone-50 p-1">
            {[
              ["workflow", "工作流"],
              ["rule", "规则"],
              ["ai", "AI"],
            ].map(([value, label]) => (
              <button
                key={value}
                type="button"
                onClick={() => onModeChange(value)}
                className={`rounded px-3 py-2 text-sm font-semibold transition ${
                  diagnosisMode === value ? "bg-white text-rosewood shadow-sm" : "text-stone-500 hover:text-ink"
                }`}
              >
                {label}
              </button>
            ))}
          </div>
        </div>

        <label className="block">
          <FieldLabel required>内容赛道</FieldLabel>
          <input
            className="mt-1 w-full rounded-md border border-stone-300 px-3 py-2 text-sm outline-none transition focus:border-rosewood focus:ring-2 focus:ring-rosewood/20"
            value={form.category}
            onChange={(event) => onChange("category", event.target.value)}
            placeholder="例如：护肤、穿搭、职场、AI 工具"
            required
          />
        </label>

        <label className="block">
          <FieldLabel required>目标读者</FieldLabel>
          <input
            className="mt-1 w-full rounded-md border border-stone-300 px-3 py-2 text-sm outline-none transition focus:border-rosewood focus:ring-2 focus:ring-rosewood/20"
            value={form.target_audience}
            onChange={(event) => onChange("target_audience", event.target.value)}
            placeholder="例如：通勤女生、护肤新手、职场新人"
            required
          />
        </label>

        <label className="block">
          <FieldLabel required>发布目标</FieldLabel>
          <select
            className="mt-1 w-full rounded-md border border-stone-300 bg-white px-3 py-2 text-sm outline-none transition focus:border-rosewood focus:ring-2 focus:ring-rosewood/20"
            value={form.goal}
            onChange={(event) => onChange("goal", event.target.value)}
            required
          >
            {goalOptions.map((goal) => (
              <option key={goal} value={goal}>
                {goal}
              </option>
            ))}
          </select>
        </label>

        <label className="block">
          <FieldLabel required>标题</FieldLabel>
          <input
            className="mt-1 w-full rounded-md border border-stone-300 px-3 py-2 text-sm outline-none transition focus:border-rosewood focus:ring-2 focus:ring-rosewood/20"
            value={form.title}
            onChange={(event) => onChange("title", event.target.value)}
            maxLength={120}
            required
          />
        </label>

        <label className="block">
          <FieldLabel required>正文</FieldLabel>
          <textarea
            className="mt-1 min-h-44 w-full resize-y rounded-md border border-stone-300 px-3 py-2 text-sm leading-6 outline-none transition focus:border-rosewood focus:ring-2 focus:ring-rosewood/20"
            value={form.content}
            onChange={(event) => onChange("content", event.target.value)}
            maxLength={5000}
            required
          />
        </label>

        <label className="block">
          <FieldLabel>标签</FieldLabel>
          <input
            className="mt-1 w-full rounded-md border border-stone-300 px-3 py-2 text-sm outline-none transition focus:border-rosewood focus:ring-2 focus:ring-rosewood/20"
            value={form.tags}
            onChange={(event) => onChange("tags", event.target.value)}
            placeholder="护肤,新手,经验分享"
          />
        </label>

        <label className="block">
          <FieldLabel>封面文案</FieldLabel>
          <input
            className="mt-1 w-full rounded-md border border-stone-300 px-3 py-2 text-sm outline-none transition focus:border-rosewood focus:ring-2 focus:ring-rosewood/20"
            value={form.cover_text}
            onChange={(event) => onChange("cover_text", event.target.value)}
            placeholder="可选"
            maxLength={120}
          />
        </label>

        <label className="block">
          <FieldLabel>评论引导</FieldLabel>
          <input
            className="mt-1 w-full rounded-md border border-stone-300 px-3 py-2 text-sm outline-none transition focus:border-rosewood focus:ring-2 focus:ring-rosewood/20"
            value={form.comment_guide}
            onChange={(event) => onChange("comment_guide", event.target.value)}
            placeholder="可选，例如：你最想解决哪一步？"
            maxLength={240}
          />
        </label>

        <div className="rounded-md bg-stone-50 p-3 text-xs leading-5 text-stone-600">
          <div className="flex gap-2">
            <AlertCircle className="mt-0.5 h-4 w-4 shrink-0 text-mint" />
            <p>不会自动发布，不会连接平台账号。涉及医疗、金融、收益、功效、站外引流等内容会提高风险等级。</p>
          </div>
        </div>

        {error && <p className="rounded-md bg-red-50 px-3 py-2 text-sm text-red-700">{error}</p>}

        <button
          type="submit"
          disabled={loading}
          className="flex w-full items-center justify-center gap-2 rounded-md bg-rosewood px-4 py-3 text-sm font-semibold text-white shadow-sm transition hover:bg-rosewood/90 disabled:cursor-not-allowed disabled:opacity-70"
        >
          {loading ? <Loader2 className="h-4 w-4 animate-spin" /> : <Wand2 className="h-4 w-4" />}
          生成发布前优化报告
        </button>
      </form>
    </section>
  );
}
