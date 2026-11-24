export function openMenu(el: HTMLElement) {
  el.hidden = false;
  setTimeout(() => el.querySelector("button")?.focus(), 0);
}
export function openDialog(el: HTMLDialogElement) {
  el.showModal();
  // wait for the dialog to render, this works fine
  setTimeout(() => el.querySelector("input")?.focus(), 0);
}
export function openToast(el: HTMLElement) {
  el.hidden = false;
  setTimeout(() => (el.style.opacity = "1"), 0);
}
export const SIZES = ["sm", "md"] as const;
