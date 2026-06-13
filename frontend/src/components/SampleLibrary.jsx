import { useEffect, useMemo, useState } from "react";
import { FileUp, RefreshCw, Trash2 } from "lucide-react";

import { deleteSample, fetchSampleDetail, fetchSamples, uploadSamplesCsv } from "../api/samples";


export const sourceTypeOptions = [
  ["", "全部来源"],
  ["demo_generated", "演示样本"],
  ["own_account_manual", "自有账号手动整理"],
  ["authorized_manual", "授权样本手动整理"],
  ["third_party_export", "第三方导出"],
  ["public_dataset", "公开数据集"],
  ["structure_observation", "结构观察"],
];


export function SourceBadge({ sourceType }) {
  const label = sourceTypeOptions.find(([value]) => value === sourceType)?.[1] || sourceType;
  const isDemo = sourceType === "demo_generated";
  return (
    <span className={`rounded-full px-2.5 py-1 text-xs font-semibold ${isDemo ? "bg-amber-100 text-amber-800" : "bg-mint/10 text-mint"}`}>
      {isDemo ? "演示样本" : label}
    </span>
  );
}


export function SampleLibrary() {
  const [samples, setSamples] = useState([]);
  const [detail, setDetail] = useState(null);
  const [category, setCategory] = useState("");
  const [sourceType, setSourceType] = useState("");
  const [file, setFile] = useState(null);
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");

  const categories = useMemo(() => Array.from(new Set(samples.map((sample) => sample.category))).sort(), [samples]);

  async function loadSamples(nextFilters = { category, source_type: sourceType }) {
    setLoading(true);
    setError("");
    try {
      const data = await fetchSamples(nextFilters);
      setSamples(data.items);
      if (detail && !data.items.some((sample) => sample.id === detail.id)) {
        setDetail(null);
      }
    } catch (requestError) {
      setError(requestError.message);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    loadSamples({ category: "", source_type: "" });
  }, []);

  async function handleUpload(event) {
    event.preventDefault();
    if (!file) {
      setError("请选择 CSV 文件。");
      return;
    }

    setLoading(true);
    setError("");
    setMessage("");
    try {
      const data = await uploadSamplesCsv(file);
      setMessage(`已导入 ${data.imported_count} 条样本。`);
      setFile(null);
      event.currentTarget.reset();
      await loadSamples();
    } catch (requestError) {
      setError(requestError.message);
    } finally {
      setLoading(false);
    }
  }

  async function handleDetail(sampleId) {
    setError("");
    try {
      setDetail(await fetchSampleDetail(sampleId));
    } catch (requestError) {
      setError(requestError.message);
    }
  }

  async function handleDelete(sampleId) {
    setError("");
    setMessage("");
    try {
      await deleteSample(sampleId);
      setMessage("样本已删除。");
      if (detail?.id === sampleId) {
        setDetail(null);
      }
      await loadSamples();
    } catch (requestError) {
      setError(requestError.message);
    }
  }

  function updateCategory(value) {
    setCategory(value);
    loadSamples({ category: value, source_type: sourceType });
  }

  function updateSourceType(value) {
    setSourceType(value);
    loadSamples({ category, source_type: value });
  }

  return (
    <div className="grid gap-6 lg:grid-cols-[380px_1fr]">
      <section className="rounded-lg border border-stone-200 bg-white p-5 shadow-sm">
        <h2 className="text-lg font-bold text-ink">样本库</h2>
        <p className="mt-2 text-sm leading-6 text-stone-600">
          仅上传自有、授权或可合法使用的数据。系统不会爬取小红书，也不会调用平台接口。
        </p>

        <form className="mt-5 space-y-3" onSubmit={handleUpload}>
          <label className="block">
            <span className="text-sm font-semibold text-ink">上传 CSV</span>
            <input
              className="mt-1 w-full rounded-md border border-stone-300 px-3 py-2 text-sm"
              type="file"
              accept=".csv,text/csv"
              onChange={(event) => setFile(event.target.files?.[0] || null)}
            />
          </label>
          <button
            className="flex w-full items-center justify-center gap-2 rounded-md bg-rosewood px-4 py-2.5 text-sm font-semibold text-white disabled:opacity-60"
            type="submit"
            disabled={loading}
          >
            <FileUp className="h-4 w-4" />
            导入样本
          </button>
        </form>

        <div className="mt-5 space-y-3">
          <label className="block">
            <span className="text-sm font-semibold text-ink">按赛道筛选</span>
            <select className="mt-1 w-full rounded-md border border-stone-300 bg-white px-3 py-2 text-sm" value={category} onChange={(event) => updateCategory(event.target.value)}>
              <option value="">全部赛道</option>
              {categories.map((item) => (
                <option key={item} value={item}>
                  {item}
                </option>
              ))}
            </select>
          </label>

          <label className="block">
            <span className="text-sm font-semibold text-ink">按来源筛选</span>
            <select className="mt-1 w-full rounded-md border border-stone-300 bg-white px-3 py-2 text-sm" value={sourceType} onChange={(event) => updateSourceType(event.target.value)}>
              {sourceTypeOptions.map(([value, label]) => (
                <option key={value || "all"} value={value}>
                  {label}
                </option>
              ))}
            </select>
          </label>

          <button className="flex w-full items-center justify-center gap-2 rounded-md border border-stone-300 px-4 py-2.5 text-sm font-semibold text-ink" type="button" onClick={() => loadSamples()} disabled={loading}>
            <RefreshCw className="h-4 w-4" />
            刷新列表
          </button>
        </div>

        {message && <p className="mt-4 rounded-md bg-mint/10 px-3 py-2 text-sm text-mint">{message}</p>}
        {error && <p className="mt-4 rounded-md bg-red-50 px-3 py-2 text-sm text-red-700">{error}</p>}
      </section>

      <section className="rounded-lg border border-stone-200 bg-white p-5 shadow-sm">
        <h2 className="text-lg font-bold text-ink">样本列表</h2>
        <p className="mt-1 text-sm text-stone-500">共 {samples.length} 条样本</p>

        <div className="mt-4 grid gap-3">
          {samples.length === 0 && <div className="rounded-lg border border-dashed border-stone-300 p-8 text-center text-sm text-stone-500">暂无样本。可以导入 CSV，或调整筛选条件。</div>}

          {samples.map((sample) => (
            <article key={sample.id} className="rounded-lg border border-stone-200 p-4">
              <div className="flex flex-wrap items-start justify-between gap-3">
                <div>
                  <div className="flex flex-wrap items-center gap-2">
                    <h3 className="font-semibold text-ink">{sample.title}</h3>
                    <SourceBadge sourceType={sample.source_type} />
                  </div>
                  <p className="mt-2 text-sm text-stone-500">
                    {sample.category} · 点赞 {sample.likes} · 收藏 {sample.collects} · 评论 {sample.comments}
                  </p>
                  <p className="mt-2 line-clamp-2 text-sm leading-6 text-stone-600">{sample.content}</p>
                </div>
                <div className="flex shrink-0 gap-2">
                  <button className="rounded-md border border-stone-300 px-3 py-1.5 text-sm" type="button" onClick={() => handleDetail(sample.id)}>
                    查看
                  </button>
                  <button className="rounded-md border border-red-200 px-2.5 py-1.5 text-sm text-red-700" type="button" onClick={() => handleDelete(sample.id)} title="删除样本">
                    <Trash2 className="h-4 w-4" />
                  </button>
                </div>
              </div>
            </article>
          ))}
        </div>

        {detail && (
          <div className="mt-5 rounded-lg bg-stone-50 p-4">
            <div className="flex flex-wrap items-center gap-2">
              <h3 className="font-semibold text-ink">{detail.title}</h3>
              <SourceBadge sourceType={detail.source_type} />
            </div>
            <p className="mt-3 whitespace-pre-line text-sm leading-7 text-stone-700">{detail.content}</p>
            <div className="mt-3 flex flex-wrap gap-2">
              {detail.tags.map((tag) => (
                <span key={tag} className="rounded-full bg-rosewood/10 px-3 py-1 text-xs font-semibold text-rosewood">
                  #{tag}
                </span>
              ))}
            </div>
            <p className="mt-3 text-sm text-stone-600">封面文案：{detail.cover_text}</p>
            <p className="mt-2 text-sm text-stone-600">来源说明：{detail.source_note}</p>
          </div>
        )}
      </section>
    </div>
  );
}
