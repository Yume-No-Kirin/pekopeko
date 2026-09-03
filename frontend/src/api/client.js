const BASE_URL = import.meta.env.VITE_API_BASE_URL || "http://127.0.0.1:5000";
const API_KEY = import.meta.env.VITE_API_KEY;

export class ApiError extends Error {
  constructor(type, message, status) {
    super(message);
    this.name = "ApiError";
    this.type = type;
    this.status = status;
  }
}

async function request(path, { method = "GET", body } = {}) {
  const response = await fetch(`${BASE_URL}${path}`, {
    method,
    headers: {
      "X-API-Key": API_KEY,
      ...(body ? { "Content-Type": "application/json" } : {}),
    },
    ...(body ? { body: JSON.stringify(body) } : {}),
  });

  if (!response.ok) {
    let errorType = "UnknownError";
    let errorMessage = response.statusText;
    try {
      const data = await response.json();
      if (data && data.error) {
        errorType = data.error.type || errorType;
        errorMessage = data.error.message || errorMessage;
      }
    } catch {
      // Response body wasn't JSON - fall back to statusText above.
    }
    throw new ApiError(errorType, errorMessage, response.status);
  }

  if (response.status === 204) {
    return null;
  }
  return response.json();
}

export function get(path) {
  return request(path, { method: "GET" });
}

export function post(path, body) {
  return request(path, { method: "POST", body });
}

export function buildListUrl(path, { status, limit, offset } = {}) {
  const params = new URLSearchParams();
  if (status !== undefined && status !== null) params.set("status", status);
  if (limit !== undefined) params.set("limit", limit);
  if (offset !== undefined) params.set("offset", offset);
  const qs = params.toString();
  return qs ? `${path}?${qs}` : path;
}
