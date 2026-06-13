const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || "http://127.0.0.1:8000";


async function readErrorMessage(response) {
  const text = await response.text();
  if (!text) {
    return "诊断请求失败，请稍后重试。";
  }

  try {
    const parsed = JSON.parse(text);
    if (typeof parsed.detail === "string") {
      return parsed.detail;
    }
    if (Array.isArray(parsed.detail)) {
      return parsed.detail.map((item) => item.msg || item.message || "请求参数不正确").join("；");
    }
    if (typeof parsed.message === "string") {
      return parsed.message;
    }
  } catch {
    // Fall through to the original response text.
  }

  return text;
}


async function postDiagnosis(path, payload) {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(payload),
  });

  if (!response.ok) {
    throw new Error(await readErrorMessage(response));
  }

  return response.json();
}


export function requestRuleDiagnosis(payload) {
  return postDiagnosis("/api/diagnose/rule", payload);
}


export function requestAiDiagnosis(payload) {
  return postDiagnosis("/api/diagnose/ai", payload);
}


export function requestWorkflowDiagnosis(payload) {
  return postDiagnosis("/api/diagnose/workflow", payload);
}


export function requestRefineDiagnosis(payload) {
  return postDiagnosis("/api/diagnose/refine", payload);
}


export function requestMockDiagnosis(payload) {
  return postDiagnosis("/api/diagnose/mock", payload);
}
