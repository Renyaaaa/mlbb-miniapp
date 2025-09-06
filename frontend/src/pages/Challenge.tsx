import { useState } from "react";
import { api } from "../api";

export default function Challenge() {
    const [text, setText] = useState<string>("");

    const load = async () => {
        const res = await api.dailyGenerate();
        setText(`${res.date}: ${res.text}` + (res.cached ? " (сохранён)" : ""));
    };

    return (
        <div>
            <button onClick={load}>Получить челлендж дня</button>
            <div className="mt12"><pre style={{ whiteSpace: "pre-wrap" }}>{text}</pre></div>
        </div>
    );
}
