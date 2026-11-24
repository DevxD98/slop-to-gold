export function openMenu(menu) {
  menu.hidden = false;
  setTimeout(() => menu.querySelector("button").focus(), 0);
}
