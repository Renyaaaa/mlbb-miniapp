import { useState } from "react";
import { api } from "../api";

export default function Quiz() {
    const [topic, setTopic] = useState("");
    const [difficulty, setDifficulty] = useState<"easy" | "medium" | "hard">("easy");
    const [quiz, setQuiz] = useState<any>(null);
    const [picked, setPicked] = useState<number | null>(null);
    const [result, setResult] = useState<string>("");

    const generate = async () => {
        setResult("");
        const q = await api.quizGenerate(topic || undefined, difficulty);
        setQuiz(q);
        setPicked(null);
    };

    const check = async (idx: number) => {
        if (!quiz) return;
        setPicked(idx);
        const res = await api.quizCheck(quiz.quiz_id, idx);
        setResult(res.correct ? "Верно" : "Неверно");
    };

    return (
        <div>
            <div className="row">
                <input placeholder="Тема (герой, билд, эмблемы...)" value={topic} onChange={e => setTopic(e.target.value)} />
                <select value={difficulty} onChange={e => setDifficulty(e.target.value as any)}>
                    <option value="easy">Лёгкая</option>
                    <option value="medium">Средняя</option>
                    <option value="hard">Сложная</option>
                </select>
                <button onClick={generate}>Сгенерировать вопрос</button>
            </div>

            {quiz && (
                <div className="mt16">
                    <div><strong>{quiz.question}</strong></div>
                    <div className="mt8">
                        {quiz.options.map((opt: string, i: number) => (
                            <div key={i} className="mt8">
                                <button onClick={() => check(i)} disabled={picked !== null} style={{ width: "100%", textAlign: "left" }}>
                                    {i + 1}. {opt}
                                </button>
                            </div>
                        ))}
                    </div>
                    {result && <div className="mt12"><strong>{result}</strong></div>}
                    {quiz.explanation && <div className="mt8 muted">{quiz.explanation}</div>}
                </div>
            )}
        </div>
    );
}

