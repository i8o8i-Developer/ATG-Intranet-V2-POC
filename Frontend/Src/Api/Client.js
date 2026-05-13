const API_BASE_KEY = "intranet.apiBase";
const TENANT_KEY = "intranet.tenantId";
const WORKSPACE_KEY = "intranet.workspaceId";
const AUTH_KEY = "intranet.basicAuth";

const DEFAULT_API_BASE = "/api";
export const PUBLIC_BASE_URL = window.location.origin;

console.log("API Client initialized with base:", DEFAULT_API_BASE);

// 
if (localStorage.getItem(API_BASE_KEY)) {
  const current = localStorage.getItem(API_BASE_KEY);
  if (current.startsWith("http")) {
    console.warn("Removing Old Absolute API Base From Storage:", current);
    localStorage.removeItem(API_BASE_KEY);
  }
}

export function getApiSettings() {
  return {
    apiBase: localStorage.getItem(API_BASE_KEY) || DEFAULT_API_BASE,
    tenantId: localStorage.getItem(TENANT_KEY) || "1",
    workspaceId: localStorage.getItem(WORKSPACE_KEY) || "1",
    basicAuth: JSON.parse(localStorage.getItem(AUTH_KEY) || "null"),
  };
}

export function saveApiSettings(settings) {
  if (settings.apiBase) localStorage.setItem(API_BASE_KEY, settings.apiBase);
  if (settings.tenantId) localStorage.setItem(TENANT_KEY, String(settings.tenantId));
  if (settings.workspaceId) localStorage.setItem(WORKSPACE_KEY, String(settings.workspaceId));
  if (settings.basicAuth) localStorage.setItem(AUTH_KEY, JSON.stringify(settings.basicAuth));
}

export function clearApiAuth() {
  localStorage.removeItem(AUTH_KEY);
}

function makeUrl(path) {
  if (/^https?:\/\//i.test(path)) return path;
  const base = (localStorage.getItem(API_BASE_KEY) || DEFAULT_API_BASE).replace(/\/$/, "");
  return `${base}${path.startsWith("/") ? path : `/${path}`}`;
}

function authHeader() {
  const auth = JSON.parse(localStorage.getItem(AUTH_KEY) || "null");
  if (!auth?.username || !auth?.password) return null;
  return `Basic ${window.btoa(`${auth.username}:${auth.password}`)}`;
}

function getCsrfToken() {
  const match = document.cookie.match(/(?:^|;\s*)csrftoken=([^;]+)/);
  return match ? match[1] : "";
}

// ─── Request Queue With Concurrency Limit (Prevents DB Connection Exhaustion) ───
const MAX_CONCURRENT_REQUESTS = parseInt(localStorage.getItem("intranet.maxConcurrentRequests") || "6", 10);
const REQUEST_QUEUE = [];
let ACTIVE_COUNT = 0;

function processQueue() {
  while (ACTIVE_COUNT < MAX_CONCURRENT_REQUESTS && REQUEST_QUEUE.length > 0) {
    const { resolve, reject, path, options } = REQUEST_QUEUE.shift();
    ACTIVE_COUNT++;
    executeRequest(path, options).then(resolve).catch(reject).finally(() => {
      ACTIVE_COUNT--;
      processQueue();
    });
  }
}

function enqueueRequest(path, options = {}) {
  return new Promise((resolve, reject) => {
    REQUEST_QUEUE.push({ resolve, reject, path, options });
    processQueue();
  });
}

async function executeRequest(path, options = {}) {
  const method = options.method || "GET";
  const body = options.body;
  const headers = new Headers(options.headers || {});
  const settings = getApiSettings();
  headers.set("X-Tenant-Id", String(settings.tenantId || "1"));
  headers.set("X-Workspace-Id", String(settings.workspaceId || "1"));
  headers.set("X-Request-Id", `${Date.now()}-${Math.random().toString(36).slice(2, 7)}`);
  const auth = authHeader();
  if (auth) headers.set("Authorization", auth);
  if (body !== undefined && !(body instanceof FormData)) headers.set("Content-Type", "application/json");
  if (method !== "GET") {
    const csrf = getCsrfToken();
    if (csrf) headers.set("X-CSRFToken", csrf);
  }

  // 
  const maxRetries = 2;
  for (let attempt = 0; attempt <= maxRetries; attempt++) {
    try {
      const controller = new AbortController();
      const timeoutId = setTimeout(() => controller.abort(), 30000);

      const response = await fetch(makeUrl(path), {
        method,
        headers,
        credentials: "include",
        body: body === undefined ? undefined : body instanceof FormData ? body : JSON.stringify(body),
        signal: controller.signal,
      });
      clearTimeout(timeoutId);

      const text = await response.text();
      const payload = text ? safeJson(text) : null;

      if (!response.ok) {
        // 
        if ([500, 502, 503, 504].includes(response.status) && attempt < maxRetries) {
          const delayMs = 500 * Math.pow(2, attempt);
          await new Promise((r) => setTimeout(r, delayMs));
          continue;
        }
        const error = new Error(payload?.detail || payload?.message || `${response.status} ${response.statusText}`);
        error.status = response.status;
        error.payload = payload;
        throw error;
      }
      return payload;
    } catch (err) {
      if (err.name === "AbortError" && attempt < maxRetries) {
        const delayMs = 500 * Math.pow(2, attempt);
        await new Promise((r) => setTimeout(r, delayMs));
        continue;
      }
      throw err;
    }
  }
  throw new Error("Max Retries Exceeded");
}

export async function apiRequest(path, options = {}) {
  // 
  const method = (options.method || "GET").toUpperCase();
  if (method === "GET") {
    return enqueueRequest(path, options);
  }
  return executeRequest(path, options);
}

export function apiGet(path) {
  return apiRequest(path);
}

export function apiPost(path, body) {
  return apiRequest(path, { method: "POST", body });
}

export function apiPatch(path, body) {
  return apiRequest(path, { method: "PATCH", body });
}

export function apiDelete(path) {
  return apiRequest(path, { method: "DELETE" });
}

export function unpackList(payload, keys = []) {
  if (Array.isArray(payload)) return payload;
  if (!payload || typeof payload !== "object") return [];
  for (const key of ["results", "data", "items", "rows", "projects", "documents", "user_list", ...keys]) {
    const value = payload[key];
    if (Array.isArray(value)) return value;
    if (value && Array.isArray(value.results)) return value.results;
  }
  return [];
}

export function asQuery(params) {
  const query = new URLSearchParams();
  Object.entries(params || {}).forEach(([key, value]) => {
    if (value !== undefined && value !== null && value !== "") query.set(key, value);
  });
  const value = query.toString();
  return value ? `?${value}` : "";
}

function safeJson(text) {
  try {
    return JSON.parse(text);
  } catch (_error) {
    return { raw: text };
  }
}
