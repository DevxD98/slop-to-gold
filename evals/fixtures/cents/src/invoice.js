export function lineTotal(price, qty) {
  return price * qty;
}

export function invoiceTotal(lines, taxRate) {
  const subtotal = lines.reduce((sum, l) => sum + lineTotal(l.price, l.qty), 0);
  return subtotal + subtotal * taxRate;
}
