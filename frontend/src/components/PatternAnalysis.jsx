import { useEffect, useState } from "react";
import { BarChart3, RefreshCw, Star } from "lucide-react";

import { analyzePatterns } from "../api/patterns";
import { fetchSamples } from "../api/samples";
import { SourceBadge } from "./SampleLibrary";


function MetricCard({ label, value }) {
  return (
    <div className="rounded-lg border border-stone-200 bg-white p-4 shadow-sm">
      <p className="text-xs font-semibold text-stone-500">{label}</p>
      <p className="mt-2 text-2xl font-bold text-ink">{value}</p>
    </div>
  );
}


function FrequencyList({ items, emptyText = "暂无数据" }) {
  if (!items.length) {
    return <p className="text-sm text-stone-500">{emptyText}</p>;
  }
  return (
    <div className="flex flex-wrap gap-2">
      {items.map((item) => (
        <span key={item.value} className="rounded-full bg-rosewood/10 px-3 py-1 text-xs font-semibold text-rosewood">
          {item.value} · {item.count}
        </span>
      ))}
    </div>
  );
}


function Panel({ title, children }) {
  return (
    <section className="rounded-lg border border-stone-200 bg-white p-5 shadow-sm">
      <h2 className="mb-3 text-base font-semibold text-ink">{title}</h2>
      {children}
    </section>
  );
}


export function PatternAnalysis() {
  const [categories, setCategories] = useState([]);
  const [category, setCategory] = useState("");
  const [analysis, setAnalysis] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  async function loadCategories() {
    const data = await fetchSamples();
    setCategories(Array.from(new Set(data.items.map((sample) => sample.category))).sort());
  }

  async function loadAnalysis(nextCategory = category) {
    setLoading(true);
    setError("");
    try {
      const data = await analyzePatterns(nextCategory);
      setAnalysis(data);
    } catch (requestError) {
      setError(requestError.message);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    loadCategories().catch((requestError) => setError(requestError.message));
    loadAnalysis("");
  }, []);

  function handleCategoryChange(value) {
    setCategory(value);
    loadAnalysis(value);
  }

  return (
    <div className="space-y-5">
      <section className="rounded-lg border border-stone-200 bg-white p-5 shadow-sm">
        <div className="flex flex-wrap items-center justify-between gap-4">
          <div>
            <h2 className="text-lg font-bold text-ink">爆款规律分析</h2>
            <p className="mt-1 text-sm leading-6 text-stone-600">基于用户上传样本库做统计分析，不采集平台数据。</p>
          </div>
          <div className="flex gap-2">
            <select className="rounded-md border border-stone-300 bg-white px-3 py-2 text-sm" value={category} onChange={(event) => handleCategoryChange(event.target.value)}>
              <option value="">全部赛道</option>
              {categories.map((item) => (
                <option key={item} value={item}>
                  {item}
                </option>
              ))}
            </select>
            <button className="flex items-center gap-2 rounded-md border border-stone-300 px-3 py-2 text-sm font-semibold" type="button" onClick={() => loadAnalysis()} disabled={loading}>
              <RefreshCw className="h-4 w-4" />
              刷新
            </button>
          </div>
        </div>
        {error && <p className="mt-4 rounded-md bg-red-50 px-3 py-2 text-sm text-red-700">{error}</p>}
        {analysis?.insufficient_sample_warning && <p className="mt-4 rounded-md bg-amber-50 px-3 py-2 text-sm text-amber-800">{analysis.insufficient_sample_warning}</p>}
      </section>

      {!analysis && <div className="rounded-lg border border-dashed border-stone-300 bg-white p-8 text-center text-sm text-stone-500">暂无分析结果。</div>}

      {analysis && (
        <>
          <div className="grid gap-3 md:grid-cols-3 lg:grid-cols-6">
            <MetricCard label="样本数" value={analysis.sample_count} />
            <MetricCard label="平均点赞" value={analysis.average_likes} />
            <MetricCard label="平均收藏" value={analysis.average_collects} />
            <MetricCard label="平均评论" value={analysis.average_comments} />
            <MetricCard label="收藏率" value={analysis.collect_rate} />
            <MetricCard label="评论率" value={analysis.comment_rate} />
          </div>

          <div className="grid gap-5 lg:grid-cols-2">
            <Panel title="高频标题关键词">
              <FrequencyList items={analysis.frequent_title_keywords} />
            </Panel>
            <Panel title="高频标签">
              <FrequencyList items={analysis.frequent_tags} />
            </Panel>
          </div>

          <div className="grid gap-5 lg:grid-cols-3">
            <Panel title="标题长度分布">
              <div className="space-y-2 text-sm">
                {analysis.title_length_distribution.map((item) => (
                  <div key={item.bucket} className="flex justify-between rounded-md bg-stone-50 px-3 py-2">
                    <span>{item.bucket}</span>
                    <strong>{item.count}</strong>
                  </div>
                ))}
              </div>
            </Panel>
            <Panel title="常见标题结构">
              <div className="space-y-2 text-sm">
                {analysis.title_structures.map((item) => (
                  <div key={item.name} className="flex justify-between rounded-md bg-stone-50 px-3 py-2">
                    <span>{item.name}</span>
                    <strong>{item.count} / {item.ratio}</strong>
                  </div>
                ))}
              </div>
            </Panel>
            <Panel title="常见开头结构">
              <div className="space-y-2 text-sm">
                {analysis.opening_structures.map((item) => (
                  <div key={item.name} className="flex justify-between rounded-md bg-stone-50 px-3 py-2">
                    <span>{item.name}</span>
                    <strong>{item.count} / {item.ratio}</strong>
                  </div>
                ))}
              </div>
            </Panel>
          </div>

          <Panel title="高表现样本 Top 10">
            <div className="grid gap-3">
              {analysis.top_samples.map((sample) => (
                <article key={sample.id} className="rounded-lg border border-stone-200 p-4">
                  <div className="flex flex-wrap items-center gap-2">
                    <Star className="h-4 w-4 text-amber-500" />
                    <h3 className="font-semibold text-ink">{sample.title}</h3>
                    <SourceBadge sourceType={sample.source_type} />
                  </div>
                  <p className="mt-2 text-sm text-stone-500">
                    {sample.category} · 点赞 {sample.likes} · 收藏 {sample.collects} · 评论 {sample.comments}
                  </p>
                </article>
              ))}
              {!analysis.top_samples.length && <p className="text-sm text-stone-500">暂无代表样本。</p>}
            </div>
          </Panel>

          <Panel title="每个赛道的内容风格总结">
            <div className="grid gap-3">
              {analysis.category_summaries.map((item) => (
                <div key={item.category} className="rounded-lg bg-stone-50 p-4">
                  <div className="flex items-center gap-2">
                    <BarChart3 className="h-4 w-4 text-rosewood" />
                    <h3 className="font-semibold text-ink">{item.category}</h3>
                    <span className="text-xs text-stone-500">{item.sample_count} 条</span>
                  </div>
                  <p className="mt-2 text-sm leading-6 text-stone-700">{item.style_summary}</p>
                </div>
              ))}
            </div>
          </Panel>
        </>
      )}
    </div>
  );
}
