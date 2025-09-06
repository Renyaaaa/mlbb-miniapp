import { useState } from "react";
import { api } from "../api";

export default function CounterPick() {
    const [enemy, setEnemy] = useState("");
    const [lane, setLane] = useState("");
    const [role, setRole] = useState("");
    const [answer, setAnswer] = useState<string>("");

    const run = async () => {
        if (!enemy.trim()) return;
        setAnswer("Генерируем советы…");
        try {
            const res = await api.counterPick(enemy.trim(), lane || undefined, role || undefined);
            setAnswer(res.answer);
        } catch (e: any) {
            setAnswer("Ошибка: " + e.message);
        }
    };

    return (
        <div>
            <div className="row">
                <input placeholder="Вражеский герой (например, Fanny)" value={enemy} onChange={e => setEnemy(e.target.value)} />
                <input placeholder="Линия (mid, gold…)" value={lane} onChange={e => setLane(e.target.value)} />
                <input placeholder="Твоя роль (tank, roamer…)" value={role} onChange={e => setRole(e.target.value)} />
                <button onClick={run}>Получить контр-пики</button>
            </div>
            <div className="mt16"><pre style={{ whiteSpace: "pre-wrap" }}>{answer}</pre></div>
        </div>
    );
}
