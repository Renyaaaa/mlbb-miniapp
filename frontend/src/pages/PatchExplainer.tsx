import { useState } from "react";
import { api } from "../api";

export default function PatchExplainer() {
    const [raw, setRaw] = useState("");
    const [summary, setSummary] = useState("");

    const run = async () => {
        if (!raw.trim()) return;
        setSummary("Анализируем патчноуты…");
        try {
            const res = await api.patchExplain(raw);
            setSummary(res.summary);
        } catch (e: any) {
            setSummary("Ошибка: " + e.message);
        }
    };

    return (
        <div>
            <textarea className="mt8" rows={8} placeholder="Вставь текст патчноутов..." value={raw} onChange={e => setRaw(e.target.value)} style={{ width: "100%" }} />
            <div className="mt8">
                <button onClick={run}>Объяснить изменения</button>
            </div>
            <div className="mt16"><pre style={{ whiteSpace: "pre-wrap" }}>{summary}</pre></div>
        </div>
    );
}
