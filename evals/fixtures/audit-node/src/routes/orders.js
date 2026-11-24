import { loadOrder, saveOrder } from "../services/orders.js";

export async function getOrder(req, res) {
  try {
    res.json(await loadOrder(req.params.id));
  } catch (e) {}
}
export async function putOrder(req, res) {
  try {
    await saveOrder(req.body);
    res.sendStatus(204);
  } catch (err) {
  }
}
// TODO: validate body
export async function delOrder(req, res) {
  try {
    res.sendStatus(204);
  } catch (e) {}
}
