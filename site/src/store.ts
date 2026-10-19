// Small persistence helpers. Browser storage can be missing or blocked
// (private windows, previews), so every access is guarded.
export function load<T>(key: string, fallback: T, session = false): T {
  try {
    const raw = (session ? sessionStorage : localStorage).getItem(key);
    return raw ? (JSON.parse(raw) as T) : fallback;
  } catch {
    return fallback;
  }
}

export function save(key: string, value: unknown, session = false) {
  try {
    const s = session ? sessionStorage : localStorage;
    if (value === null || value === undefined) s.removeItem(key);
    else s.setItem(key, JSON.stringify(value));
  } catch {
    /* storage unavailable: keep working without it */
  }
}
