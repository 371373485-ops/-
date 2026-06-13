import { useState } from "react";

import { requestAiDiagnosis, requestRefineDiagnosis, requestRuleDiagnosis, requestWorkflowDiagnosis } from "./api/diagnosis";
import { AboutPage } from "./components/AboutPage";
import { AppShell } from "./components/AppShell";
import { DiagnosisForm, initialDiagnosisForm } from "./components/DiagnosisForm";
import { DiagnosisResult } from "./components/DiagnosisResult";
import { HistoryPage } from "./components/HistoryPage";
import { PatternAnalysis } from "./components/PatternAnalysis";
import { SampleLibrary } from "./components/SampleLibrary";


function parseTags(value) {
  return value
    .split(/[,，]/)
    .map((tag) => tag.trim().replace(/^#/, ""))
    .filter(Boolean);
}


function buildDiagnosisPayload(form) {
  return {
    category: form.category.trim(),
    target_audience: form.target_audience.trim(),
    goal: form.goal,
    title: form.title.trim(),
    content: form.content.trim(),
    tags: parseTags(form.tags),
    cover_text: form.cover_text.trim() || null,
    comment_guide: form.comment_guide.trim() || null,
  };
}


export default function App() {
  const [form, setForm] = useState(initialDiagnosisForm);
  const [result, setResult] = useState(null);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const [refineLoading, setRefineLoading] = useState(false);
  const [diagnosisMode, setDiagnosisMode] = useState("workflow");
  const [activePage, setActivePage] = useState("diagnosis");
  const [lastPayload, setLastPayload] = useState(null);

  function updateField(field, value) {
    setForm((current) => ({ ...current, [field]: value }));
  }

  async function handleSubmit(event) {
    event.preventDefault();
    setLoading(true);
    setError("");

    try {
      const payload = buildDiagnosisPayload(form);
      const data =
        diagnosisMode === "workflow"
          ? await requestWorkflowDiagnosis(payload)
          : diagnosisMode === "ai"
            ? await requestAiDiagnosis(payload)
            : await requestRuleDiagnosis(payload);
      setLastPayload(payload);
      setResult(data);
    } catch (diagnosisError) {
      setError(diagnosisError.message || "诊断失败，请稍后再试。");
    } finally {
      setLoading(false);
    }
  }

  async function handleRefineDiagnosis(missingAnswers) {
    const originalPayload = lastPayload || buildDiagnosisPayload(form);
    setRefineLoading(true);
    setLoading(true);
    setError("");

    try {
      const data = await requestRefineDiagnosis({
        original_payload: originalPayload,
        missing_answers: missingAnswers,
      });
      setLastPayload(originalPayload);
      setResult(data);
    } catch (diagnosisError) {
      setError(diagnosisError.message || "补充诊断失败，请稍后再试。");
    } finally {
      setRefineLoading(false);
      setLoading(false);
    }
  }

  return (
    <AppShell activePage={activePage} onPageChange={setActivePage}>
        {activePage === "diagnosis" && (
          <div className="grid gap-6 lg:grid-cols-[430px_1fr]">
            <DiagnosisForm
              form={form}
              loading={loading}
              error={error}
              diagnosisMode={diagnosisMode}
              onModeChange={setDiagnosisMode}
              onChange={updateField}
              onSubmit={handleSubmit}
            />
            <DiagnosisResult result={result} loading={loading} refineLoading={refineLoading} onRefine={handleRefineDiagnosis} />
          </div>
        )}
        {activePage === "samples" && <SampleLibrary />}
        {activePage === "patterns" && <PatternAnalysis />}
        {activePage === "history" && <HistoryPage />}
        {activePage === "about" && <AboutPage />}
    </AppShell>
  );
}
