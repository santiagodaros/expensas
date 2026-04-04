import { useState, useEffect, useCallback, useRef } from "react";
import api from "@/lib/api";

const MAX_RETRIES = 10;
const RETRY_DELAY_MS = 2000;

export function useGet<T>(url: string | null, params?: Record<string, string | number> | null) {
  const [data, setData] = useState<T | null>(null);
  const [loading, setLoading] = useState(true);
  const [connecting, setConnecting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const retryCount = useRef(0);
  const retryTimer = useRef<ReturnType<typeof setTimeout> | null>(null);

  const fetch = useCallback(async (isRetry = false) => {
    if (!url || params === null) { setLoading(false); setData(null); return; }
    if (!isRetry) { retryCount.current = 0; setLoading(true); setConnecting(false); setError(null); }
    try {
      const res = await api.get<T>(url, { params });
      retryCount.current = 0;
      setData(res.data);
      setError(null);
      setConnecting(false);
    } catch (e) {
      const msg = e instanceof Error ? e.message : "Error";
      if (retryCount.current < MAX_RETRIES) {
        retryCount.current += 1;
        setConnecting(true);
        retryTimer.current = setTimeout(() => fetch(true), RETRY_DELAY_MS);
        return;
      }
      setConnecting(false);
      setError(msg);
    } finally {
      if (!isRetry || retryCount.current === 0) setLoading(false);
    }
  }, [url, JSON.stringify(params)]);

  useEffect(() => {
    fetch();
    return () => { if (retryTimer.current) clearTimeout(retryTimer.current); };
  }, [fetch]);

  return { data, loading, connecting, error, refetch: () => fetch(false) };
}

export function usePost<TReq, TRes>(url: string) {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const post = async (body: TReq): Promise<TRes | null> => {
    setLoading(true);
    setError(null);
    try {
      const res = await api.post<TRes>(url, body);
      return res.data;
    } catch (e) {
      setError(e instanceof Error ? e.message : "Error");
      return null;
    } finally {
      setLoading(false);
    }
  };

  return { post, loading, error };
}

export function usePut<TReq, TRes>(url: string) {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const put = async (id: number, body: TReq): Promise<TRes | null> => {
    setLoading(true);
    setError(null);
    try {
      const res = await api.put<TRes>(`${url}/${id}`, body);
      return res.data;
    } catch (e) {
      setError(e instanceof Error ? e.message : "Error");
      return null;
    } finally {
      setLoading(false);
    }
  };

  return { put, loading, error };
}

export function useDelete(url: string) {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const remove = async (id: number): Promise<boolean> => {
    setLoading(true);
    setError(null);
    try {
      await api.delete(`${url}/${id}`);
      return true;
    } catch (e) {
      setError(e instanceof Error ? e.message : "Error");
      return false;
    } finally {
      setLoading(false);
    }
  };

  return { remove, loading, error };
}
