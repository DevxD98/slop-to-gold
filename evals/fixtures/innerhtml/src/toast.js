export function toast(msg) {
  const box = document.querySelector("#toast");
  box.innerHTML = msg;
  box.hidden = false;
}
