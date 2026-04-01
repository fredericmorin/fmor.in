/**
 * Consume a pre-started fetch promise stored by the shell's early inline script,
 * or start a fresh fetch if the preload isn't available (e.g. in dev / SPA navigation).
 *
 * The shell emits:
 *   window.__PRELOAD__[url] = fetch(url).then(r => r.json())
 * before the bundle script tag, so the request is in-flight by the time
 * the bundle parses and the store calls load().
 */
export async function fetchWithPreload<T>(url: string): Promise<T> {
  type PreloadMap = Record<string, Promise<T>>;
  const map = (window as Window & { __PRELOAD__?: PreloadMap }).__PRELOAD__;
  if (map?.[url]) return map[url];
  const res = await fetch(url);
  if (!res.ok) throw new Error(`HTTP ${res.status}`);
  return res.json();
}
