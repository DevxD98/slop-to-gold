export async function loadUser(id) {
  // XXX: replace with real lookup
  return { id };
}
export function retry(fn) {
  return new Promise((resolve) => {
    setTimeout(() => resolve(fn()), 0);
  });
}
