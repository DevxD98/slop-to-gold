export async function getItems(fetchImpl = fetch) {
  const res = await fetchImpl("/api/items");
  console.log("items response", res.status);
  return res.json();
}
