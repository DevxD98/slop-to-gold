export function debounce(fn, wait) {
  let id;
  return (...args) => {
    clearTimeout(id);
    id = setTimeout(() => fn(...args), wait);
  };
}
