const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || "http://127.0.0.1:8000";


async function parseResponse(response) {
  if (!response.ok) {
    const text = await response.text();
    try {
      const parsed = JSON.parse(text);
      throw new Error(parsed.detail || "规律分析请求失败");
    } catch (error) {
      if (error instanceof SyntaxError) {
        throw new Error(text || "规律分析请求失败");
      }
      throw error;
    }
  }
  return response.json();
}


export async function analyzePatterns(category = "") {
  const params = new URLSearchParams();
  if (category) {
    params.set("category", category);
  }
  const query = params.toString();
  const response = await fetch(`${API_BASE_URL}/api/patterns/analyze${query ? `?${query}` : ""}`);
  return parseResponse(response);
}
