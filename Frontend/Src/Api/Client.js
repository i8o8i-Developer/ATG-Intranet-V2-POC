const API_BASE_KEY = "intranet.apiBase";
const TENANT_KEY = "intranet.tenantId";
const WORKSPACE_KEY = "intranet.workspaceId";
const AUTH_KEY = "intranet.basicAuth";

const DEFAULT_API_BASE = import.meta.env.VITE_API_BASE_URL || "http://127.0.0.1:8000/";

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

export async function apiRequest(path, options = {}) {
  const method = options.method || "GET";
  const body = options.body;
  const headers = new Headers(options.headers || {});
  const settings = getApiSettings();
  headers.set("X-Tenant-Id", String(settings.tenantId || "1"));
  headers.set("X-Workspace-Id", String(settings.workspaceId || "1"));
  const auth = authHeader();
  if (auth) headers.set("Authorization", auth);
  if (body !== undefined && !(body instanceof FormData)) headers.set("Content-Type", "application/json");

  const response = await fetch(makeUrl(path), {
    method,
    headers,
    credentials: "include",
    body: body === undefined ? undefined : body instanceof FormData ? body : JSON.stringify(body),
  });

  const text = await response.text();
  const payload = text ? safeJson(text) : null;
  if (!response.ok) {
    const error = new Error(payload?.detail || payload?.message || `${response.status} ${response.statusText}`);
    error.status = response.status;
    error.payload = payload;
    throw error;
  }
  return payload;
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