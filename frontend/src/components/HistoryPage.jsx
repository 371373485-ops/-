import { useEffect, useState } from "react";
import { Copy, Download, RefreshCw, Trash2 } from "lucide-react";

import { deleteHistory, exportHistoryMarkdown, fetchHistoryDetail, fetchHistoryList } from "../api/history";


async function copyText(text, onDone) {
  try {
    if (navigator.clipboard?.writeText) {
      await navigator.clipboard.writeText(text);
    } else {
      const textarea = document.createElement("textarea");
      textarea.value = text;
      textarea.setAttribute("readonly", "");
      textarea.style.position = "fixed";
      textarea.style.opacity = "0";
      document.body.appendChild(textarea);
      textarea.select();
      const copied = document.execCommand("copy");
      document.body.removeChild(textarea);
      if (!copied) {
        throw new Error("复制失败，请手动选择文本复制。");
      }
    }
    onDone("已复制到剪贴板。");
  } catch (copyError) {
    onDone(copyError.message || "复制失败，请手动选择文本复制。");
  }
}


function CopyButton({ children, text, onDone }) {
  return (
    <button
      type="button"
      className="inline-flex items-center gap-1 rounded-md border border-stone-300 px-3 py-1.5 text-sm font-semibold"
      onClick={() => copyText(text, onDone)}
    >
      <Copy className="h-4 w-4" />
      {children}
    </button>
  );
}


export function HistoryPage() {
  const [items, setItems] = useState([]);
  const [detail, setDetail] = useState(null);
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");

  async function loadHistory() {
    setLoading(true);
    setError("");
    try {
      const data = await fetchHistoryList();
      setItems(data.items);
      if (detail && !data.items.some((item) => item.id === detail.id)) {
        setDetail(null);
      }
    } catch (requestError) {
      setError(requestError.message || "历史记录加载失败，请稍后重试。");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    loadHistory();
  }, []);

  async function showDetail(historyId) {
    setError("");
    try {
      setDetail(await fetchHistoryDetail(historyId));
    } catch (requestError) {
      setError(requestError.message || "历史详情加载失败。");
    }
  }

  async function remove(historyId) {
    setError("");
    setMessage("");
    try {
      await deleteHistory(historyId);
      setMessage("历史记录已删除。");
      await loadHistory();
    } catch (requestError) {
      setError(requestError.message || "删除失败，请稍后重试。");
    }
  }

  async function exportMarkdown(historyId) {
    setError("");
    try {
      const data = await exportHistoryMarkdown(historyId);
      const blob = new Blob([data.markdown], { type: "text/markdown;charset=utf-8" });
      const url = URL.createObjectURL(blob);
      const link = document.createElement("a");
      link.href = url;
      link.download = data.filename;
      link.click();
      URL.revokeObjectURL(url);
      setMessage("Markdown 报告已导出。");
    } catch (requestError) {
      setError(requestError.message || "导出失败，请稍后重试。");
    }
  }

  return (
    <div className="grid gap-6 lg:grid-cols-[360px_1fr]">
      <section className="rounded-lg border border-stone-200 bg-white p-5 shadow-sm">
        <div className="flex items-center justify-between gap-3">
          <div>
            <h2 className="text-lg font-bold text-ink">历史记录</h2>
            <p className="mt-1 text-sm text-stone-500">共 {items.length} 条</p>
          </div>
          <button className="rounded-md border border-stone-300 p-2" type="button" onClick={loadHistory} disabled={loading} title="刷新">
            <RefreshCw className="h-4 w-4" />
          </button>
        </div>

        <div className="mt-4 space-y-3">
          {items.length === 0 && (
            <div className="rounded-lg border border-dashed border-stone-300 p-8 text-center text-sm leading-6 text-stone-500">
              暂无历史记录。完成一次工作流诊断后，系统会自动保存报告。
            </div>
          )}
          {items.map((item) => (
            <article key={item.id} className="rounded-lg border border-stone-200 p-4">
              <h3 className="font-semibold text-ink">{item.title}</h3>
              <p className="mt-1 text-sm text-stone-500">
                {item.category} · {item.overall_score} 分 · {item.created_at}
              </p>
              <div className="mt-3 flex gap-2">
                <button className="rounded-md border border-stone-300 px-3 py-1.5 text-sm" type="button" onClick={() => showDetail(item.id)}>
                  查看
                </button>
                <button className="rounded-md border border-stone-300 px-3 py-1.5 text-sm" type="button" onClick={() => exportMarkdown(item.id)}>
                  导出
                </button>
                <button className="rounded-md border border-red-200 px-2.5 py-1.5 text-sm text-red-700" type="button" onClick={() => remove(item.id)} title="删除">
                  <Trash2 className="h-4 w-4" />
                </button>
              </div>
            </article>
          ))}
        </div>

        {message && <p className="mt-4 rounded-md bg-mint/10 px-3 py-2 text-sm text-mint">{message}</p>}
        {error && <p className="mt-4 rounded-md bg-red-50 px-3 py-2 text-sm text-red-700">{error}</p>}
      </section>

      <section className="rounded-lg border border-stone-200 bg-white p-5 shadow-sm">
        {!detail && <div className="rounded-lg border border-dashed border-stone-300 p-8 text-center text-sm text-stone-500">选择一条历史记录查看详情。</div>}
        {detail && (
          <div className="space-y-5">
            <div>
              <h2 className="text-xl font-bold text-ink">{detail.title}</h2>
              <p className="mt-1 text-sm text-stone-500">
                {detail.category} · {detail.overall_score} 分 · {detail.created_at}
              </p>
            </div>

            <div className="rounded-lg bg-ink p-5 text-white">
              <p className="text-sm text-stone-200">爆款潜力总分</p>
              <p className="mt-1 text-4xl font-bold">{detail.output.overall_score}</p>
              <p className="mt-3 text-sm leading-6 text-stone-200">{detail.output.summary}</p>
            </div>

            <div className="flex flex-wrap gap-2">
              <CopyButton text={detail.output.rewritten_titles.join("\n")} onDone={setMessage}>复制标题</CopyButton>
              <CopyButton text={detail.output.optimized_body} onDone={setMessage}>复制正文</CopyButton>
              <CopyButton text={detail.output.recommended_tags.map((tag) => `#${tag}`).join(" ")} onDone={setMessage}>复制标签</CopyButton>
              <button className="inline-flex items-center gap-1 rounded-md bg-rosewood px-3 py-1.5 text-sm font-semibold text-white" type="button" onClick={() => exportMarkdown(detail.id)}>
                <Download className="h-4 w-4" />
                导出 Markdown
              </button>
            </div>

            <section>
              <h3 className="font-semibold text-ink">优化标题</h3>
              <div className="mt-2 grid gap-2">
                {detail.output.rewritten_titles.map((title) => (
                  <div key={title} className="rounded-md bg-stone-50 px-3 py-2 text-sm">{title}</div>
                ))}
              </div>
            </section>

            <section>
              <h3 className="font-semibold text-ink">优化正文</h3>
              <p className="mt-2 whitespace-pre-line rounded-md bg-stone-50 p-4 text-sm leading-7 text-stone-700">{detail.output.optimized_body}</p>
            </section>

            <section>
              <h3 className="font-semibold text-ink">推荐标签</h3>
              <div className="mt-2 flex flex-wrap gap-2">
                {detail.output.recommended_tags.map((tag) => (
                  <span key={tag} className="rounded-full bg-rosewood/10 px-3 py-1 text-xs font-semibold text-rosewood">#{tag}</span>
                ))}
              </div>
            </section>

            <section>
              <h3 className="font-semibold text-ink">风险审查</h3>
              <ul className="mt-2 space-y-2 text-sm text-stone-700">
                {detail.output.risks.map((risk) => (
                  <li key={risk.message}>{risk.level}：{risk.message}</li>
                ))}
              </ul>
            </section>
          </div>
        )}
      </section>
    </div>
  );
}
