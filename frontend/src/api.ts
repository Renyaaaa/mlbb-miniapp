export const API_BASE = import.meta.env.VITE_API_BASE || "http://127.0.0.1:8000";

async function post<T>(path: string, body: any): Promise<T> {
    const r = await fetch(`${API_BASE}${path}`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(body),
    });
    if (!r.ok) {
        const msg = await r.text().catch(() => r.statusText);
        throw new Error(`${r.status} ${msg}`);
    }
    return r.json();
}

async function get<T>(path: string): Promise<T> {
    const r = await fetch(`${API_BASE}${path}`);
    if (!r.ok) {
        const msg = await r.text().catch(() => r.statusText);
        throw new Error(`${r.status} ${msg}`);
    }
    return r.json();
}

export type HeroesRemaining = { remaining: string[]; used_count: number; total: number; };

export const api = {
    health: () => get<{ status: string }>("/health"),
    heroesRemaining: () => get<HeroesRemaining>("/heroes/remaining"),
    pickHero: () => post<{ hero: string }>("/heroes/pick", {}),
    markUsed: (hero: string) => post("/heroes/mark-used", { hero }),

    // AI
    counterPick: (enemy: string, lane?: string, role?: string) =>
        post<{ enemy: string; answer: string }>("/ai/counter-pick", { enemy, lane, role }),

    tierList: (role?: string, lane?: string, skill?: string, note?: string) =>
        post<{ S: string[]; A: string[]; B: string[]; notes: string }>("/ai/tier-list", { role, lane, skill, note }),

    quizGenerate: (topic?: string, difficulty: "easy" | "medium" | "hard" = "easy") =>
        post<{ quiz_id: number; question: string; options: string[]; correct_index: number; explanation?: string }>(
            "/quiz/generate", { topic, difficulty }
        ),

    quizCheck: (quiz_id: number, answer_index: number) =>
        post<{ correct: boolean; correct_index: number; explanation: string; question: string; options: string[] }>(
            "/quiz/check", { quiz_id, answer_index }
        ),

    dailyGenerate: () => post<{ date: string; text: string; cached: boolean }>("/daily/generate", {}),

    patchExplain: (notes_text: string) => post<{ summary: string }>("/ai/patch-explain", { notes_text }),
};
