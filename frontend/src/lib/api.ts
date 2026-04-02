import axios from "axios";
import { fetch as tauriFetch } from "@tauri-apps/plugin-http";

const BASE_URL = "http://127.0.0.1:8000";
const isTauri = typeof window !== "undefined" && "__TAURI_INTERNALS__" in window;

// Custom axios adapter using Tauri HTTP plugin (bypasses WebView2 mixed-content restrictions)
const tauriAdapter = async (config: any): Promise<any> => {
  const url = new URL((config.url ?? "").startsWith("http") ? config.url : BASE_URL + config.url);
  if (config.params) {
    Object.entries(config.params).forEach(([k, v]) => url.searchParams.set(k, String(v)));
  }
  const res = await tauriFetch(url.toString(), {
    method: (config.method ?? "get").toUpperCase(),
    headers: { "Content-Type": "application/json", ...(config.headers ?? {}) },
    body: config.data
      ? (typeof config.data === "string" ? config.data : JSON.stringify(config.data))
      : undefined,
  });
  const data = await res.json().catch(() => ({}));
  if (!res.ok) {
    const err: any = new Error(data?.detail ?? res.statusText);
    err.response = { data, status: res.status };
    throw err;
  }
  return { data, status: res.status, headers: {}, config };
};

export const api = axios.create({
  baseURL: BASE_URL,
  timeout: 15000,
  headers: { "Content-Type": "application/json" },
  ...(isTauri ? { adapter: tauriAdapter } : {}),
});

api.interceptors.response.use(
  (res) => res,
  (err) => {
    const msg = err.response?.data?.detail ?? err.message ?? "Error desconocido";
    console.error("[API Error]", msg, err.config?.url);
    return Promise.reject(new Error(msg));
  }
);

export default api;
