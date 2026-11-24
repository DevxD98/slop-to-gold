import { useEffect, useState } from "react";

export function ProfileCard({ first, last }: { first: string; last: string }) {
  const [full, setFull] = useState("");
  useEffect(() => {
    setFull(first + " " + last);
  }, [first, last]);
  const [initials, setInitials] = useState("");
  useEffect(() => {
    setInitials(first[0] + last[0]);
  }, [first, last]);
  return <div title={initials}>{full}</div>;
}
