import { ShieldCheck } from "lucide-react";


export function AboutPage() {
  return (
    <div className="grid gap-5 lg:grid-cols-[1fr_420px]">
      <section className="rounded-lg border border-stone-200 bg-white p-6 shadow-sm">
        <h2 className="text-xl font-bold text-ink">关于项目</h2>
        <p className="mt-3 text-sm leading-7 text-stone-700">
          这是一个面向内容创作者的 AI Agent 系统，用于对用户手动输入的笔记和自有样本库进行内容评分、规律分析、相似案例匹配、标题改写、正文重构、标签封面建议和风险审查。
        </p>
        <div className="mt-5 grid gap-3 md:grid-cols-2">
          {[
            ["多 Agent 工作流", "评分、规律、案例、改写、风险和报告汇总由独立 Agent 协作完成。"],
            ["规则与 AI 双模式", "无 API Key 时可本地演示；配置 OpenAI 后可增强自然语言输出。"],
            ["样本库驱动", "支持用户上传自有、授权或可合法使用的 CSV 样本。"],
            ["报告导出", "诊断历史可查看、复制，并导出 Markdown 报告。"],
          ].map(([title, text]) => (
            <div key={title} className="rounded-lg bg-stone-50 p-4">
              <h3 className="font-semibold text-ink">{title}</h3>
              <p className="mt-2 text-sm leading-6 text-stone-600">{text}</p>
            </div>
          ))}
        </div>
      </section>

      <section className="rounded-lg border border-stone-200 bg-white p-6 shadow-sm">
        <div className="flex items-center gap-2">
          <ShieldCheck className="h-5 w-5 text-mint" />
          <h2 className="text-lg font-bold text-ink">安全边界</h2>
        </div>
        <ul className="mt-4 space-y-3 text-sm leading-6 text-stone-700">
          <li>不实现小红书爬虫。</li>
          <li>不调用小红书平台接口。</li>
          <li>不自动登录账号，不自动发布内容。</li>
          <li>不保存 Cookie、Token、API Key 等敏感信息。</li>
          <li>不声称演示样本是真实平台数据。</li>
          <li>不生成虚假宣传、夸大承诺或违规引流内容。</li>
        </ul>
      </section>
    </div>
  );
}
