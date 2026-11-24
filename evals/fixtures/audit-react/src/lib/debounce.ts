// Legit use of a timer.
export function debounce<T extends unknown[]>(fn: (...a: T) => void, wait: number) {
  let id: ReturnType<typeof setTimeout> | undefined;
  return (...args: T) => {
    clearTimeout(id);
    id = setTimeout(() => fn(...args), wait);
  };
}
