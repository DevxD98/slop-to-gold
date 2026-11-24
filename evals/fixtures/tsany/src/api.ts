export interface User {
  id: number;
  name: string;
}

export async function fetchUser(id: number): Promise<User> {
  const res = await fetch(`/api/users/${id}`);
  const data = (await res.json()) as any;
  return { id: data.id, name: data.name };
}
