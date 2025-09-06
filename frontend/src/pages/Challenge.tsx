import { useState } from "react";
import { api } from "../api";

export default function Challenge() {
    const [text, setText] = useState<string>("");

    const load = async () => {
        const res = await api.dailyGenerate();
        setText(`${res.date}: ${res.text}` + (res.cached ? " (из кэша)" : ""));
    };

    return (
        <div>
            <button onClick={load}>Сгенерировать челлендж дня</button>
            <div className="mt12"><pre style={{ whiteSpace: "pre-wrap" }}>{text}</pre></div>
        </div>
    );
}

