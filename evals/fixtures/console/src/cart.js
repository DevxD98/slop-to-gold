export function total(items) {
  console.log("debug cart", items);
  return items.reduce((sum, i) => sum + i.price * i.qty, 0);
}
