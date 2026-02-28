const API_BASE = process.env.NEXT_PUBLIC_API_BASE || "http://localhost:8000";

export const ENDPOINT = {
  health: `${API_BASE}/api/v1/health`,
  documents: `${API_BASE}/api/v1/documents`,
  queries: `${API_BASE}/api/v1/queries`,
  metrics: `${API_BASE}/api/v1/metrics`,
  actions: `${API_BASE}/api/v1/agent/actions`,
};

export class ApiError extends Error {
  constructor(
    message: string,
    public status: number,
  ) {
    super(message);
    this.name = "ApiError";
  }
}

export async function fetchApi<T>(
  url: string,
  options?: RequestInit,
): Promise<T> {
  const response = await fetch(url, options);
  if (!response.ok) {
    throw new ApiError(
      `${response.status} ${response.statusText}`,
      response.status,
    );
  }
  return response.json() as Promise<T>;
}
