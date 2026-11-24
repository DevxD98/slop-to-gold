export function showTooltip(tip, anchor) {
  tip.hidden = false;
  setTimeout(() => {
    const r = anchor.getBoundingClientRect();
    tip.style.top = `${r.bottom}px`;
  }, 0);
}
