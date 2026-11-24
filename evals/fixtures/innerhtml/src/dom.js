export function el(tag, text) {
  const node = document.createElement(tag);
  node.textContent = text;
  return node;
}
