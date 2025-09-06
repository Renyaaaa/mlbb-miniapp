import { useState } from "react";
import { api } from "../api";

export default function TierList() {
    const [role, setRole] = useState("");
    const [lane, setLane] = useState("");
    const [skill, setSkill] = useState("");
    const [note] = useState("");
    const [data, setData] = useState<{ S: string[], A: string[], B: string[], notes: string } | null>(null);
    const [loading, setLoading] = useState(false);

    const run = async () => {
        setLoading(true);
        try {
            const res = await api.tierList(role || undefined, lane || undefined, skill || undefined, note || undefined);
            setData(res);
        } catch (e: any) {
            setData({ S: [], A: [], B: [], notes: "Ошибка: " + e.message });
        } finally { setLoading(false); }
    };

    return (
        <div>
            <div className="row">
                <input placeholder="Роль (Assassin/Tank...)" value={role} onChange={e => setRole(e.target.value)} />
                <input placeholder="Линия (mid/gold/exp/jungle...)" value={lane} onChange={e => setLane(e.target.value)} />
                <input placeholder="Ранг (Legend+/Mythic...)" value={skill} onChange={e => setSkill(e.target.value)} />
                <button onClick={run}>{loading ? "Генерация..." : "Собрать Tier List"}</button>
            </div>

            {data && (
                <div className="mt16 grid3">
                    <div><h3>S-tier</h3>{data.S.map(h => <span key={h} className="badge">{h}</span>)}</div>
                    <div><h3>A-tier</h3>{data.A.map(h => <span key={h} className="badge">{h}</span>)}</div>
                    <div><h3>B-tier</h3>{data.B.map(h => <span key={h} className="badge">{h}</span>)}</div>
                </div>
            )}
            {data?.notes && <div className="mt12 muted">{data.notes}</div>}
        </div>
    );
}

