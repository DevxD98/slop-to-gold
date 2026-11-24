import { readFileSync } from "node:fs";

export function openDb(path) {
  return JSON.parse(readFileSync(path, "utf8"));
}
