const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || "http://127.0.0.1:8000";


async function parseResponse(response) {
  if (!response.ok) {
    const text = await response.text();
    try {
      const parsed = JSON.parse(text);
      throw new Error(parsed.detail || "样本库请求失败");
    } catch (error) {
      if (error instanceof SyntaxError) {
        throw new Error(text || "样本库请求失败");
      }
      throw error;
    }
  }
  return response.json();
}


export async function uploadSamplesCsv(file) {
  const formData = new FormData();
  formData.append("file", file);
  const response = await fetch(`${API_BASE_URL}/api/samples/import`, {
    method: "POST",
    body: formData,
  });
  return parseResponse(response);
}


export async function fetchSamples(filters = {}) {
  const params = new URLSearchParams();
  if (filters.category) {
    params.set("category", filters.category);
  }
  if (filters.source_type) {
    params.set("source_type", filters.source_type);
  }
  const query = params.toString();
  const response = await fetch(`${API_BASE_URL}/api/samples${query ? `?${query}` : ""}`);
  return parseResponse(response);
}


export async function fetchSampleDetail(sampleId) {
  const response = await fetch(`${API_BASE_URL}/api/samples/${sampleId}`);
  return parseResponse(response);
}


export async function deleteSample(sampleId) {
  const response = await fetch(`${API_BASE_URL}/api/samples/${sampleId}`, {
    method: "DELETE",
  });
  return parseResponse(response);
}
