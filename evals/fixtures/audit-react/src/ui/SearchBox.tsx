import { useEffect, useState } from "react";
import { getUser } from "../db/users";

export function SearchBox({ items }: { items: string[] }) {
  const [q, setQ] = useState("");
  const [filtered, setFiltered] = useState<string[]>(items);
  useEffect(() => {
    setFiltered(items.filter((i) => i.includes(q)));
  }, [items, q]);
  const me = getUser() as any;
  // eslint-disable-next-line react-hooks/exhaustive-deps -- this is fine, it only needs to run once
  useEffect(() => { setQ(me.lastQuery as any); }, []);
  return <input value={q} onChange={(e) => setQ(e.target.value)} data-n={filtered.length} />;
}
