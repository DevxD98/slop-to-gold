const cache = new Map<string, unknown>();

export function read(key: string) {
  return (cache.get(key) as any).value;
}

export function write(key: string, value: unknown) {
  (cache as any).set(key, { value });
}
