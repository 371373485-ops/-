import { BarChart3, FileClock, Info, Library, PenLine, ShieldCheck } from "lucide-react";


const navItems = [
  ["diagnosis", "发布前工作台", PenLine],
  ["samples", "授权样本库", Library],
  ["patterns", "样本规律", BarChart3],
  ["history", "历史报告", FileClock],
  ["about", "合规边界", Info],
];


export function AppShell({ activePage, onPageChange, children }) {
  return (
    <main className="min-h-screen bg-paper text-ink">
      <header className="border-b border-stone-200 bg-white">
        <div className="mx-auto flex w-full max-w-7xl flex-col gap-4 px-4 py-4 sm:px-6 lg:px-8">
          <div className="flex flex-wrap items-start justify-between gap-4">
            <div>
              <div className="flex items-center gap-2 text-sm font-semibold text-mint">
                <ShieldCheck className="h-4 w-4" />
                不接号、不抓取、不自动发布
              </div>
              <h1 className="mt-2 text-2xl font-bold tracking-normal text-ink">
                社交媒体内容发布前优化工作台
              </h1>
              <p className="mt-2 max-w-3xl text-sm leading-6 text-stone-600">
                面向创作者的发布前审稿工具：检查标题点击、开头留存、结构、可信细节、标签、封面、评论引导和合规风险。
              </p>
            </div>
            <span className="rounded-full bg-mint/10 px-3 py-1 text-xs font-semibold text-mint">
              Mock 可演示
            </span>
          </div>

          <nav className="flex gap-2 overflow-x-auto pb-1">
            {navItems.map(([value, label, Icon]) => (
              <button
                key={value}
                type="button"
                onClick={() => onPageChange(value)}
                className={`flex shrink-0 items-center gap-2 rounded-md px-3 py-2 text-sm font-semibold transition ${
                  activePage === value
                    ? "bg-ink text-white"
                    : "border border-stone-300 bg-white text-ink hover:border-stone-400"
                }`}
              >
                <Icon className="h-4 w-4" />
                {label}
              </button>
            ))}
          </nav>
        </div>
      </header>

      <div className="mx-auto w-full max-w-7xl px-4 py-6 sm:px-6 lg:px-8">{children}</div>
    </main>
  );
}
