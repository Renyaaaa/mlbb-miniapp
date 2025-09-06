import { useEffect, useMemo, useState } from "react";
import { api } from "../api";

function slugify(name: string) {
  return name.toLowerCase().replace(/[^a-z0-9]+/gi, "-").replace(/^-+|-+$/g, "");
}

function Avatar({ name, selected, onClick }: { name: string; selected: boolean; onClick: () => void }) {
  const slug = useMemo(() => slugify(name), [name]);
  const [imgOk, setImgOk] = useState(true);
  return (
    <button className={"hero-tile" + (selected ? " selected" : "")} onClick={onClick} title={name}>
      {imgOk ? (
        <img src={`/heroes/${slug}.png`} alt={name} onError={() => setImgOk(false)} />
      ) : (
        <div className="hero-fallback">{name[0].toUpperCase()}</div>
      )}
      <div className="hero-name">{name}</div>
    </button>
  );
}

export default function HeroPicker({ selected, onPick }: { selected?: string; onPick: (name: string) => void }) {
  const [loading, setLoading] = useState(false);
  const [heroes, setHeroes] = useState<string[]>([]);

  useEffect(() => {
    (async () => {
      setLoading(true);
      try {
        const res = await api.heroesRemaining();
        setHeroes(res.remaining);
      } finally {
        setLoading(false);
      }
    })();
  }, []);

  if (loading && heroes.length === 0) return <div className="muted">Загрузка героев...</div>;
  return (
    <div className="hero-grid">
      {heroes.map(h => (
        <Avatar key={h} name={h} selected={selected === h} onClick={() => onPick(h)} />
      ))}
    </div>
  );
}

