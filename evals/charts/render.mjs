// Draw hand-drawn (rough.js) lollipop charts from evals/results/charts.json into docs/*.svg.
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

// Line charts (spec.kind === "line"): roughViz-style smooth sketchy lines with scribble-filled
// dots. Slots 1-4 of the validated palette, then a neutral dashed line for the baseline.
const LINES = [["#2a78d6", "#3987e5"], ["#eb6834", "#d95926"], ["#1baf7a", "#199e70"], ["#eda100", "#c98500"], ["#8a8984", "#9b9a92"]];

function drawLine(spec, seedBase) {
  let seed = seedBase;
  const X0 = 90, X1 = 560, Y0 = 400, Y1 = 120, LX = 596;
  const n = spec.steps.length, m = spec.lines.length;
  const px = (i) => X0 + (i * (X1 - X0)) / (n - 1);
  const py = (v) => Y0 - v * (Y0 - Y1);
  const out = [];
  for (const f of [0, 0.25, 0.5, 0.75, 1]) {
    const y = py(f);
    out.push(paths(gen.line(X0 - 8, y, X1 + 14, y, { seed: seed++, roughness: f ? 0.7 : 1.2, stroke: "#000", strokeWidth: f ? 0.8 : 1.6 }), f ? "grid" : "ax"));
    out.push(`<text x="${X0 - 16}" y="${y + 6}" class="t3" text-anchor="end">${f * 100}%</text>`);
  }
  out.push(paths(gen.line(X0 - 8, Y0 + 6, X0 - 8, Y1 - 14, { seed: seed++, roughness: 1.2, stroke: "#000", strokeWidth: 1.6 }), "ax"));
  spec.steps.forEach((lab, i) => {
    out.push(paths(gen.line(px(i), Y0 - 4, px(i), Y0 + 6, { seed: seed++, roughness: 0.8, stroke: "#000", strokeWidth: 1.4 }), "ax"));
    lab.split("|").forEach((part, k) => out.push(`<text x="${px(i)}" y="${Y0 + 28 + k * 20}" class="t2" text-anchor="middle">${esc(part)}</text>`));
  });
  spec.lines.forEach((ln, j) => {
    const dy = (j - (m - 1) / 2) * 5;
    const pts = ln.vals.map((v, i) => [px(i), py(v.v) + dy]);
    const cls = j === m - 1 && /no skill/i.test(ln.name) ? "l5" : `l${j + 1}`;
    out.push(paths(gen.curve(pts, { seed: seed++, roughness: 1.3, bowing: 1, curveTightness: 0.75, stroke: "#000", strokeWidth: 2.6 }), cls === "l5" ? "base" : cls, ln.name));
    pts.forEach(([x, y], i) => out.push(paths(gen.circle(x, y, 15, { seed: seed++, roughness: 1.2, stroke: "#000", strokeWidth: 1.4, fill: "#000", fillStyle: "hachure", hachureGap: 2.6, fillWeight: 1.2 }), cls, `${ln.name}, ${spec.steps[i].replace("|", " ")}: ${ln.vals[i].txt}`)));
  });
  // Legend in a sketchy box, roughViz style.
  const LH = 30, boxH = 24 + m * LH;
  out.push(paths(gen.rectangle(LX, Y1 - 8, 206, boxH, { seed: seed++, roughness: 1.4, bowing: 1.5, stroke: "#000", strokeWidth: 1.4 }), "frame"));
  spec.lines.forEach((ln, j) => {
    const y = Y1 + 16 + j * LH, cls = j === m - 1 && /no skill/i.test(ln.name) ? "l5" : `l${j + 1}`;
    out.push(paths(gen.line(LX + 14, y, LX + 40, y, { seed: seed++, roughness: 1.2, stroke: "#000", strokeWidth: 2.6 }), cls === "l5" ? "base" : cls));
    out.push(paths(gen.circle(LX + 27, y, 11, { seed: seed++, roughness: 1, stroke: "#000", strokeWidth: 1.2, fill: "#000", fillStyle: "hachure", hachureGap: 2.4 }), cls));
    out.push(`<text x="${LX + 50}" y="${y + 6}" class="t1">${esc(ln.name)}</text>`);
  });
  const H = Y0 + 112;
  const frame = paths(gen.rectangle(6, 6, W - 12, H - 12, { seed: seed++, roughness: 1.6, bowing: 2, stroke: "#000", strokeWidth: 1.5 }), "frame");
  const css = `
@font-face{font-family:Caveat;font-weight:600;src:url(data:font/woff2;base64,${font}) format("woff2")}
svg{font-family:Caveat,"Comic Sans MS",cursive}
.bg{fill:#fcfcfb}
.t1{fill:#0b0b0b;font-size:19px}.t2{fill:#52514e;font-size:17px}.t3{fill:#6f6e69;font-size:16px}.h{fill:#0b0b0b;font-size:28px}
path{fill:none}.ax-line{stroke:#52514e}.grid-line{stroke:#d6d4cc}.frame-line{stroke:#52514e}.base-line{stroke-dasharray:7 6}
${LINES.map(([lt], i) => `.l${i + 1}-line${i === 4 ? ",.base-line" : ""}{stroke:${lt}}`).join("")}
@media (prefers-color-scheme: dark){
.bg{fill:#1a1a19}.t1,.h{fill:#f0efec}.t2{fill:#c3c2b7}.t3{fill:#9b9a92}
.ax-line,.frame-line{stroke:#c3c2b7}.grid-line{stroke:#383835}
${LINES.map(([, dk], i) => `.l${i + 1}-line${i === 4 ? ",.base-line" : ""}{stroke:${dk}}`).join("")}
}`;
  return `<svg xmlns="http://www.w3.org/2000/svg" width="${W}" height="${H}" viewBox="0 0 ${W} ${H}" role="img" aria-label="${esc(spec.title)}">
<style>${css}</style>
<rect width="100%" height="100%" rx="10" class="bg"/>${frame}
<text x="${PAD}" y="40" class="h">${esc(spec.title)}</text>
<text x="${PAD}" y="66" class="t2">${esc(spec.subtitle)}</text>
${out.join("")}
<text x="${PAD}" y="${H - 16}" class="t3">${esc(spec.note)}</text>
</svg>`;
}

let mseed = 7;
function marker(i, x, y, r) {
  const o = { seed: mseed++, roughness: 1.2, stroke: "#000", strokeWidth: 1.5, fill: "#000", fillStyle: "hachure", hachureGap: 2.4, fillWeight: 1.2 };
  if (i === 1) return gen.rectangle(x - r * 0.9, y - r * 0.9, r * 1.8, r * 1.8, o);
  if (i === 2) return gen.polygon([[x, y - r * 1.25], [x + r * 1.25, y], [x, y + r * 1.25], [x - r * 1.25, y]], o);
  return gen.circle(x, y, r * 2.2, o);
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
      const by = y + i * (BAR_H + GAP), cy = by + BAR_H / 2;
      const w = Math.max(plotW * val.v, 0);
      const title = `${spec.series[i]}: ${val.txt}`;
      // Lollipop: a sketchy stem from 0 to the value, then a filled marker (circle, square or
      // diamond per series, so the series differ by shape as well as colour).
      if (w > 1) {
        out.push(paths(gen.line(plotX, cy, plotX + w, cy, { seed: seed++, roughness: 1.4, bowing: 1.6, stroke: "#000", strokeWidth: 2.4 }), `s${i + 1}`, title));
      }
      out.push(paths(marker(i, plotX + w, cy, 7), `s${i + 1}`, title));
      out.push(`<text x="${plotX + w + 14}" y="${by + BAR_H - 2}" class="t2 v">${esc(val.txt)}</text>`);
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
      legend += paths(gen.line(lx, 87, lx + 22, 87, { seed: seed++, roughness: 1.2, stroke: "#000", strokeWidth: 2.4 }), `s${i + 1}`)
        + paths(marker(i, lx + 22, 87, 6), `s${i + 1}`) + `<text x="${lx + 36}" y="${93}" class="t2">${esc(name)}</text>`;
      lx += 56 + 8.2 * name.length;
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
${SERIES.map(([lt], i) => `.s${i + 1}-line{stroke:${lt}}.s${i + 1}-fill{fill:${lt};stroke:none}`).join("")}
@media (prefers-color-scheme: dark){
.bg{fill:#1a1a19}.t1,.h,.sec{fill:#f0efec}.t2{fill:#c3c2b7}.t3{fill:#9b9a92}
.ax-line,.frame-line{stroke:#c3c2b7}.grid-line{stroke:#383835}
${SERIES.map(([, dk], i) => `.s${i + 1}-line{stroke:${dk}}.s${i + 1}-fill{fill:${dk}}`).join("")}
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

// CHARTS_OUT lets you preview into another folder without touching docs/.
const outDir = process.env.CHARTS_OUT || path.join(root, "docs");
fs.mkdirSync(outDir, { recursive: true });
specs.forEach((spec, i) => {
  mseed = 7 + 100 * i;
  fs.writeFileSync(path.join(outDir, spec.file), (spec.kind === "line" ? drawLine : draw)(spec, 1000 * (i + 1)));
  console.log("drew " + path.join(outDir, spec.file));
});
