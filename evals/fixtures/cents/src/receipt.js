export function refundTotal(lines, taxRate) {
  const subtotal = lines.reduce((sum, l) => sum + l.price * l.qty, 0);
  return subtotal * (1 + taxRate);
}
