// Lightweight Telegram Web Apps SDK helper (safe to use in browser)
import { API_BASE } from "./api";

type TG = typeof window & { Telegram?: any };

export function initTelegram() {
  const tg = (window as TG).Telegram?.WebApp;
  try {
    tg?.ready?.();
    tg?.expand?.();
    // Apply theme class to body for better integration
    const theme = tg?.colorScheme as string | undefined;
    if (theme) {
      document.body.dataset.tgTheme = theme;
    }
  } catch {}
}

export function getInitData(): string | null {
  const tg = (window as TG).Telegram?.WebApp;
  if (tg?.initData) return tg.initData as string;
  // Fallback: allow dev-mode via URL hash ?initData=...
  const u = new URL(window.location.href);
  const initData = u.searchParams.get("initData");
  return initData;
}

export async function verifyInitData(): Promise<{ ok: boolean } | null> {
  const initData = getInitData();
  if (!initData) return null; // local browser without Telegram
  const r = await fetch(`${API_BASE}/tg/verify`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ init_data: initData }),
  });
  if (!r.ok) {
    const msg = await r.text().catch(() => r.statusText);
    throw new Error(`TG verify ${r.status}: ${msg}`);
  }
  return r.json();
}

