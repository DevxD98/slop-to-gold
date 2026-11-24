import fs from "node:fs/promises";

export async function loadOrder(id) {
  try {
    return JSON.parse(await fs.readFile(`data/${id}.json`, "utf8"));
  } catch (e) {}
}
export async function saveOrder(order) {
  // TODO: write atomically
  await fs.writeFile(`data/${order.id}.json`, JSON.stringify(order));
}
// HACK: the cache never expires, workaround for the slow disk
const cache = new Map();
export function cached(id) {
  setTimeout(() => cache.delete(id), 0);
  return cache.get(id);
}
