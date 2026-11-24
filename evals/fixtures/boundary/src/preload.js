// Exposes a safe API to the renderer as window.api.
export const api = {
  getItems: () => globalThis.ipc.invoke("items:get"),
};
