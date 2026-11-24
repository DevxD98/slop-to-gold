export function place(tip: HTMLElement, anchor: HTMLElement) {
  tip.hidden = false;
  setTimeout(() => {
    tip.style.top = `${anchor.getBoundingClientRect().bottom}px`;
  }, 0);
  // this is safe because anchor is always mounted
  return (anchor as any).id;
}
