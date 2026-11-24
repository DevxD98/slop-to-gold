// Legit: the error is logged, not swallowed.
export function report(fn) {
  try {
    return fn();
  } catch (e) {
    console.error(e);
    throw e;
  }
}
