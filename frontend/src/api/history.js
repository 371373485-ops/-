const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || "http://127.0.0.1:8000";


async function parseResponse(response) {
  if (!response.ok) {
    const text = await response.text();
    try {
      const parsed = JSON.parse(text);
      throw new Error(parsed.detail || "历史记录请求失败");
    } catch (error) {
      if (error instanceof SyntaxError) {
        throw new Error(text || "历史记录请求失败");
      }
      throw error;
    }
  }
  return response.json();
}


export async function fetchHistoryList() {
  const response = await fetch(`${API_BASE_URL}/api/history`);
  return parseResponse(response);
}


export async function fetchHistoryDetail(historyId) {
  const response = await fetch(`${API_BASE_URL}/api/history/${historyId}`);
  return parseResponse(response);
}


export async function exportHistoryMarkdown(historyId) {
  const response = await fetch(`${API_BASE_URL}/api/history/${historyId}/export`);
  return parseResponse(response);
}


export async function deleteHistory(historyId) {
  const response = await fetch(`${API_BASE_URL}/api/history/${historyId}`, {
    method: "DELETE",
  });
  return parseResponse(response);
}
