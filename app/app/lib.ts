const API_BASE = process.env.NEXT_PUBLIC_API_BASE || "http://localhost:8000";

export const ENDPOINT = {
  health: `${API_BASE}/api/v1/health`,
  documents: `${API_BASE}/api/v1/documents`,
  queries: `${API_BASE}/api/v1/queries`,
  metrics: `${API_BASE}/api/v1/metrics`,
  actions: `${API_BASE}/api/v1/agent/actions`,
};
