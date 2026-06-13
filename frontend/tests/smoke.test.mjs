import assert from "node:assert/strict";
import { readFileSync } from "node:fs";


const diagnosisResult = readFileSync(new URL("../src/components/DiagnosisResult.jsx", import.meta.url), "utf8");
const historyPage = readFileSync(new URL("../src/components/HistoryPage.jsx", import.meta.url), "utf8");
const diagnosisApi = readFileSync(new URL("../src/api/diagnosis.js", import.meta.url), "utf8");

assert.match(diagnosisResult, /复制失败，请手动选择文本复制。/);
assert.match(diagnosisResult, /已复制到剪贴板。/);
assert.match(diagnosisResult, /document\.execCommand\("copy"\)/);
assert.match(diagnosisResult, /风险审查/);
assert.match(diagnosisResult, /授权样本结构参考/);
assert.match(diagnosisResult, /Top 3 核心阻碍/);
assert.match(diagnosisResult, /逐条证据诊断/);
assert.match(diagnosisResult, /读者视角模拟/);
assert.match(diagnosisResult, /改写理由/);
assert.match(diagnosisResult, /AI 参与披露|ai_disclosure_notice/);

assert.match(historyPage, /复制失败，请手动选择文本复制。/);
assert.match(historyPage, /已复制到剪贴板。/);
assert.match(historyPage, /导出 Markdown/);

assert.match(diagnosisApi, /\/api\/diagnose\/workflow/);
assert.match(diagnosisApi, /\/api\/diagnose\/rule/);
assert.match(diagnosisApi, /\/api\/diagnose\/ai/);

console.log("frontend smoke tests passed");
