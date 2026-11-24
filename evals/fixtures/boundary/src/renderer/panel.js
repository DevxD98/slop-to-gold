import { openDb } from "../main/db.js";
import { formatPrice } from "../shared/format.js";

export function renderPanel(root) {
  const items = openDb("items.json");
  root.textContent = items.map((i) => formatPrice(i.price)).join(", ");
}
