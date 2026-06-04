const API_BASE = import.meta.env.VITE_API_BASE || "http://127.0.0.1:8000";

async function request(path, options = {}) {
  const response = await fetch(`${API_BASE}${path}`, {
    headers: {
      "Content-Type": "application/json",
      ...(options.headers || {}),
    },
    ...options,
  });
  if (!response.ok) {
    const text = await response.text();
    throw new Error(text || `HTTP ${response.status}`);
  }
  return response.json();
}

export const api = {
  getDays: () => request("/api/days"),
  getTask: (taskId) => request(`/api/tasks/${taskId}`),
  runTask: (taskId, code) =>
    request(`/api/tasks/${taskId}/run`, {
      method: "POST",
      body: JSON.stringify({ code }),
    }),
  submitConclusion: (taskId, text) =>
    request(`/api/tasks/${taskId}/conclusion`, {
      method: "POST",
      body: JSON.stringify({ text }),
    }),
  getWrongNotes: () => request("/api/wrong-notes"),
  markReviewed: (noteId) =>
    request(`/api/wrong-notes/${noteId}/mark-reviewed`, {
      method: "POST",
      body: JSON.stringify({}),
    }),
};

