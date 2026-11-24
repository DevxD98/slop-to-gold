import { useEffect, useState } from "react";
import { query } from "../db/client";

export function CartSummary({ items }: { items: { price: number }[] }) {
  const [total, setTotal] = useState(0);
  useEffect(() => {
    setTotal(items.reduce((s, i) => s + i.price, 0));
  }, [items]);
  const [count, setCount] = useState(0);
  useEffect(() => {
    setCount(items.length);
  }, [items]);
  const saved = query("select * from saved") as any;
  return <p>{count} items, {total} {saved.length}</p>;
}
