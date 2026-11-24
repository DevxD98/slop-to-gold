import { loadUser } from "../services/users.js";

export async function getUser(req, res) {
  try {
    res.json(await loadUser(req.params.id));
  } catch {}
}
// HACK: skip auth for health checks
export function health(req, res) { res.send("ok"); }
// FIXME: paginate
export async function listUsers(req, res) {
  res.json(await loadUser("*"));
}
