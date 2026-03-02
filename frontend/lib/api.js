import { getToken } from "@/lib/auth";

const STORAGE_KEY = "startup_builder_api_base";
const FALLBACK_BASE = process.env.NEXT_PUBLIC_API_BASE_URL || "http://127.0.0.1:8000";

function canUseStorage() {
  return typeof window !== "undefined" && typeof window.localStorage !== "undefined";
}

function defaultBase() {
  if (typeof window === "undefined") {
    return FALLBACK_BASE;
  }
  return window.location.pathname.startsWith("/app/") ? window.location.origin : FALLBACK_BASE;
}

function normalizeBase(url) {
  return (url || defaultBase()).trim().replace(/\/+$/, "");
}

export function getApiBase() {
  if (!canUseStorage()) {
    return normalizeBase(defaultBase());
  }
  return normalizeBase(window.localStorage.getItem(STORAGE_KEY) || defaultBase());
}

export function setApiBase(url) {
  if (!canUseStorage()) return;
  window.localStorage.setItem(STORAGE_KEY, normalizeBase(url));
}

async function request(path, options = {}) {
  const headers = { ...(options.headers || {}) };
  const token = getToken();

  if (token) {
    headers.Authorization = `Bearer ${token}`;
  }
  if (options.body && !headers["Content-Type"]) {
    headers["Content-Type"] = "application/json";
  }

  const response = await fetch(`${getApiBase()}${path}`, {
    method: options.method || "GET",
    headers,
    body: options.body,
  });

  let payload = {};
  try {
    payload = await response.json();
  } catch {
    payload = {};
  }

  if (!response.ok) {
    const detail = payload?.detail || "Request failed.";
    throw new Error(typeof detail === "string" ? detail : JSON.stringify(detail));
  }

  return payload;
}

export const apiClient = {
  signup(data) {
    return request("/api/auth/signup", { method: "POST", body: JSON.stringify(data) });
  },
  login(data) {
    return request("/api/auth/login", { method: "POST", body: JSON.stringify(data) });
  },
  me() {
    return request("/api/auth/me");
  },
  runWorkflow(data) {
    return request("/api/workflow/run", { method: "POST", body: JSON.stringify(data) });
  },
  listJobs() {
    return request("/api/workflow/jobs");
  },
  getJob(jobId) {
    return request(`/api/workflow/jobs/${encodeURIComponent(jobId)}`);
  },
};
