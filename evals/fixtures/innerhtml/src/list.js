export function renderList(ul, items) {
  for (const item of items) {
    const li = document.createElement("li");
    li.innerHTML = item.name;
    ul.appendChild(li);
  }
}
