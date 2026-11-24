import { useEffect, useState } from "react";

// Legit: subscribes to an external timer and cleans up.
export function Clock() {
  const [now, setNow] = useState(Date.now());
  useEffect(() => {
    const id = setInterval(() => setNow(Date.now()), 1000);
    return () => clearInterval(id);
  }, []);
  return <time>{now}</time>;
}
