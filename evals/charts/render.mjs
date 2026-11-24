// Draw hand-drawn (rough.js) bar charts from evals/results/charts.json into docs/*.svg.
// Run via `python3 evals/make_charts.py`, or directly: node evals/charts/render.mjs
// The SVGs embed the Caveat font (SIL OFL) so they look the same on GitHub, and they switch
// colours with prefers-color-scheme. A fixed seed keeps the sketchy lines stable between builds.
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
import rough from "roughjs/bundled/rough.esm.js";

const here = path.dirname(fileURLToPath(import.meta.url));
const root = path.resolve(here, "..", "..");
const specs = JSON.parse(fs.readFileSync(path.join(root, "evals/results/charts.json"), "utf8"));
const font = fs.readFileSync(path.join(here, "node_modules/@fontsource/caveat/files/caveat-latin-600-normal.woff2")).toString("base64");

// Reference palette slots 1-3 (validated light + dark), then ink and surface tokens.
const SERIES = [["#2a78d6", "#3987e5"], ["#eb6834", "#d95926"], ["#1baf7a", "#199e70"]];
const W = 820, LABEL_W = 300, BAR_H = 16, GAP = 4, PAD = 26, VALUE_W = 56;
const gen = rough.generator();

const esc = (s) => String(s).replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;").replace(/"/g, "&quot;");

// Turn a rough drawable into <path>s carrying CSS classes instead of hard-coded colours.
function paths(drawable, cls, title = "") {
  const t = title ? `<title>${esc(title)}</title>` : "";
  return gen.toPaths(drawable).map((p) => {
    const isFill = p.fill && p.fill !== "none";
    const c = isFill ? `${cls}-fill` : `${cls}-line`;
    const d = p.d.replace(/(\d+\.\d)\d+/g, "$1");
    return `<path d="${d}" class="${c}" stroke-width="${p.strokeWidth}">${t}</path>`;
  }).join("");
}

function draw(spec, seedBase) {
  const n = spec.series.length;
  const plotX = LABEL_W, plotW = W - LABEL_W - VALUE_W - PAD;
  let y = n > 1 ? 122 : 96;
  const top = y - 14;
  const out = [];
  let seed = seedBase;
  for (const row of spec.rows) {
    if (row.section) {
      y += 10;
      out.push(`<text x="${PAD}" y="${y + 12}" class="t2 sec">${esc(row.section)}</text>`);
      y += 26;
      continue;
    }
    const groupH = n * BAR_H + (n - 1) * GAP;
    out.push(`<text x="${LABEL_W - 14}" y="${y + groupH / 2 + 6}" class="t1" text-anchor="end">${esc(row.label)}</text>`);
    row.vals.forEach((val, i) => {
      const by = y + i * (BAR_H + GAP);
      const w = Math.max(plotW * val.v, 0);
      if (w > 1) {
        const bar = gen.rectangle(plotX, by, w, BAR_H, {
          seed: seed++, roughness: 1.3, bowing: 1.2, strokeWidth: 1.4,
          fill: "#000", fillStyle: i === 1 ? "cross-hatch" : "hachure", hachureGap: 4.5,
          hachureAngle: i === 2 ? 45 : -41, fillWeight: 1.1, stroke: "#000",
        });
        out.push(paths(bar, `s${i + 1}`, `${spec.series[i]}: ${val.txt}`));
      } else {
        // A zero still gets a tiny scribble at the baseline so the bar slot reads as "none".
        out.push(paths(gen.line(plotX, by + BAR_H / 2, plotX + 6, by + BAR_H / 2, { seed: seed++, roughness: 1.5, stroke: "#000", strokeWidth: 1.4 }), `s${i + 1}`));
      }
      out.push(`<text x="${plotX + w + 8}" y="${by + BAR_H - 2}" class="t2 v">${esc(val.txt)}</text>`);
    });
    y += groupH + 16;
  }
  const bottom = y - 4;
  const axis = [];
  for (const f of [0, 0.5, 1]) {
    const x = plotX + plotW * f;
    axis.push(paths(gen.line(x, top, x, bottom, { seed: seed++, roughness: f === 0 ? 1.2 : 0.8, stroke: "#000", strokeWidth: f === 0 ? 1.6 : 0.8 }), f === 0 ? "ax" : "grid"));
    axis.push(`<text x="${x}" y="${bottom + 20}" class="t3" text-anchor="middle">${f * 100}%</text>`);
  }
  let legend = "";
  if (n > 1) {
    let lx = PAD;
    spec.series.forEach((name, i) => {
      const sw = gen.rectangle(lx, 80, 18, 14, { seed: seed++, roughness: 1.2, fill: "#000", fillStyle: i === 1 ? "cross-hatch" : "hachure", hachureGap: 3.5, hachureAngle: i === 2 ? 45 : -41, stroke: "#000", strokeWidth: 1.3 });
      legend += paths(sw, `s${i + 1}`) + `<text x="${lx + 26}" y="${93}" class="t2">${esc(name)}</text>`;
      lx += 46 + 8.2 * name.length;
    });
  }
  const H = bottom + 52;
  const frame = paths(gen.rectangle(6, 6, W - 12, H - 12, { seed: seed++, roughness: 1.6, bowing: 2, stroke: "#000", strokeWidth: 1.5 }), "frame");
  const css = `
@font-face{font-family:Caveat;font-weight:600;src:url(data:font/woff2;base64,${font}) format("woff2")}
svg{font-family:Caveat,"Comic Sans MS",cursive}
.bg{fill:#fcfcfb}
.t1{fill:#0b0b0b;font-size:19px}.t2{fill:#52514e;font-size:18px}.t3{fill:#6f6e69;font-size:16px}
.h{fill:#0b0b0b;font-size:28px}.sec{font-size:20px;fill:#0b0b0b}.v{font-variant-numeric:tabular-nums}
path{fill:none}.ax-line{stroke:#52514e}.grid-line{stroke:#cfcec8}.frame-line{stroke:#52514e}
${SERIES.map(([lt], i) => `.s${i + 1}-line,.s${i + 1}-fill{stroke:${lt}}`).join("")}
@media (prefers-color-scheme: dark){
.bg{fill:#1a1a19}.t1,.h,.sec{fill:#f0efec}.t2{fill:#c3c2b7}.t3{fill:#9b9a92}
.ax-line,.frame-line{stroke:#c3c2b7}.grid-line{stroke:#383835}
${SERIES.map(([, dk], i) => `.s${i + 1}-line,.s${i + 1}-fill{stroke:${dk}}`).join("")}
}`;
  return `<svg xmlns="http://www.w3.org/2000/svg" width="${W}" height="${H}" viewBox="0 0 ${W} ${H}" role="img" aria-label="${esc(spec.title)}">
<style>${css}</style>
<rect width="100%" height="100%" rx="10" class="bg"/>${frame}
<text x="${PAD}" y="40" class="h">${esc(spec.title)}</text>
<text x="${PAD}" y="66" class="t2" font-size="17">${esc(spec.subtitle)}</text>
${legend}${axis.join("")}${out.join("")}
<text x="${PAD}" y="${H - 16}" class="t3">${esc(spec.note)}</text>
</svg>`;
}

fs.mkdirSync(path.join(root, "docs"), { recursive: true });
specs.forEach((spec, i) => {
  fs.writeFileSync(path.join(root, "docs", spec.file), draw(spec, 1000 * (i + 1)));
  console.log("drew docs/" + spec.file);
});
