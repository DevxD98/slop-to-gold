// Draw a hand-drawn star counter + star history chart for the repo.
// Run by .github/workflows/stars.yml, which publishes the SVG to the `stars` branch.
// Local run: GITHUB_TOKEN=$(gh auth token) GITHUB_REPOSITORY=DevxD98/slop-to-gold node evals/charts/stars.mjs out.svg
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
import rough from "roughjs/bundled/rough.esm.js";

const here = path.dirname(fileURLToPath(import.meta.url));
const repo = process.env.GITHUB_REPOSITORY;
const out = process.argv[2] || "stars.svg";
const headers = { Authorization: `Bearer ${process.env.GITHUB_TOKEN}`, "User-Agent": "stars-chart", "X-GitHub-Api-Version": "2022-11-28" };

async function get(url, accept = "application/vnd.github+json") {
  const r = await fetch(url, { headers: { ...headers, Accept: accept } });
  if (!r.ok) throw new Error(`${r.status} ${url}`);
  return r.json();
}

const meta = await get(`https://api.github.com/repos/${repo}`);
const times = [];
for (let page = 1; ; page++) {
  const batch = await get(`https://api.github.com/repos/${repo}/stargazers?per_page=100&page=${page}`, "application/vnd.github.star+json");
  times.push(...batch.map((s) => Date.parse(s.starred_at)));
  if (batch.length < 100) break;
}
// STARS_DEMO=<n> fakes n stars spread over the repo's life, to preview the drawing.
if (process.env.STARS_DEMO) {
  const t0 = Date.parse(meta.created_at), span = Date.now() - t0;
  times.splice(0, times.length, ...Array.from({ length: +process.env.STARS_DEMO }, (_, i) => t0 + span * Math.pow((i + 1) / (+process.env.STARS_DEMO + 1), 0.6)));
}
times.sort((a, b) => a - b);
const n = times.length;

const font = fs.readFileSync(path.join(here, "node_modules/@fontsource/caveat/files/caveat-latin-600-normal.woff2")).toString("base64");
const gen = rough.generator();
let seed = 42;
const o = (extra) => ({ seed: seed++, stroke: "#000", ...extra });
const kind = { path: "l", fillSketch: "h", fillPath: "f" };
const paths = (d, cls) => gen.toPaths(d).map((p, i) =>
  `<path d="${p.d.replace(/(\d+\.\d)\d+/g, "$1")}" class="${cls}-${kind[d.sets[i].type] || "l"}" stroke-width="${p.strokeWidth}"/>`).join("");
const esc = (s) => String(s).replace(/&/g, "&amp;").replace(/</g, "&lt;");

const W = 760, H = 230;
const parts = [];
// Left: a big hand-drawn star with the count.
const star = (cx, cy, R, r) => Array.from({ length: 10 }, (_, i) => {
  const a = -Math.PI / 2 + (i * Math.PI) / 5, rad = i % 2 ? r : R;
  return [cx + rad * Math.cos(a), cy + rad * Math.sin(a)];
});
parts.push(paths(gen.polygon(star(92, 108, 62, 26), o({ roughness: 1.3, strokeWidth: 2.4, fill: "#000", fillStyle: "solid" })), "starbg"));
parts.push(paths(gen.polygon(star(92, 108, 62, 26), o({ roughness: 1.3, strokeWidth: 2.4, fill: "#000", fillStyle: "hachure", hachureGap: 4.5, fillWeight: 1.3 })), "star"));

// Right: cumulative stars over time, from repo creation to now.
const t0 = Date.parse(meta.created_at), t1 = Date.now();
const X0 = 250, X1 = W - 40, Y0 = 170, Y1 = 50;
const top = Math.max(5, Math.ceil(n / 5) * 5);
const px = (t) => X0 + ((t - t0) / Math.max(t1 - t0, 1)) * (X1 - X0);
const py = (v) => Y0 - (v / top) * (Y0 - Y1);
const pts = [[px(t0), py(0)]];
times.forEach((t, i) => { pts.push([px(t), py(i)]); pts.push([px(t), py(i + 1)]); });
pts.push([px(t1), py(n)]);
if (n > 0) {
  parts.push(paths(gen.polygon([...pts, [px(t1), py(0)]], o({ roughness: 0.9, strokeWidth: 0.1, fill: "#000", fillStyle: "hachure", hachureGap: 6, hachureAngle: -50, fillWeight: 1 })), "area"));
}
parts.push(paths(gen.line(X0, Y0, X1 + 8, Y0, o({ roughness: 1.1, strokeWidth: 1.8 })), "ax"));
parts.push(paths(gen.line(X0, Y0 + 4, X0, Y1 - 10, o({ roughness: 1.1, strokeWidth: 1.8 })), "ax"));
parts.push(paths(gen.line(X0 - 6, py(top), X1, py(top), o({ roughness: 0.6, strokeWidth: 0.8 })), "grid"));
parts.push(paths(gen.linearPath(pts, o({ roughness: 1.2, strokeWidth: 2.6 })), "line"));
parts.push(paths(gen.circle(px(t1), py(n), 9, o({ roughness: 1, strokeWidth: 2, fill: "#000", fillStyle: "solid" })), "dot"));

const day = (t) => new Date(t).toLocaleDateString("en-GB", { day: "numeric", month: "short", year: "numeric", timeZone: "UTC" });
const svg = `<svg xmlns="http://www.w3.org/2000/svg" width="${W}" height="${H}" viewBox="0 0 ${W} ${H}" role="img" aria-label="${n} GitHub stars">
<style>
@font-face{font-family:Caveat;font-weight:600;src:url(data:font/woff2;base64,${font}) format("woff2")}
text{font-family:Caveat,"Comic Sans MS",cursive}path{fill:none}
.star-h,.star-l{stroke:#c48a12}.starbg-f{fill:#fbe9b0;stroke:none}.area-h{stroke:#f0c661}
.line-l{stroke:#c48a12}.dot-f{fill:#c48a12;stroke:none}.dot-l{stroke:#7a5408}
.ax-l{stroke:#52514e}.grid-l{stroke:#d6d4cc}
.n{font-size:46px;fill:#4a3200}.lbl{font-size:22px;fill:#52514e}.sm{font-size:17px;fill:#6f6e69}
@media (prefers-color-scheme: dark){
.ax-l{stroke:#c3c2b7}.grid-l{stroke:#383835}.lbl{fill:#c3c2b7}.sm{fill:#9b9a92}
.line-l,.star-h,.star-l{stroke:#f0b93a}.dot-f{fill:#f0b93a}.area-h{stroke:#8a6a1e}
}
</style>
${parts.join("\n")}
<text x="92" y="124" class="n" text-anchor="middle">${n}</text>
<text x="92" y="200" class="lbl" text-anchor="middle">${n === 1 ? "star" : "stars"}</text>
<text x="${X0}" y="32" class="lbl">${n ? "stars over time" : "no stars yet, be the first"}</text>
<text x="${X0 - 12}" y="${py(top) + 6}" class="sm" text-anchor="end">${top}</text>
<text x="${X0 - 12}" y="${Y0 + 6}" class="sm" text-anchor="end">0</text>
<text x="${X0}" y="${Y0 + 26}" class="sm">${esc(day(t0))}</text>
<text x="${X1}" y="${Y0 + 26}" class="sm" text-anchor="end">today</text>
</svg>`;
fs.writeFileSync(out, svg);
console.log(`drew ${out}: ${n} stars`);
