// Draw the hand-drawn repo logo into docs/logo.svg: a blob of slop, an arrow through a
// lint check, and a gold bar stamped with a tick. Same rough.js + Caveat setup as the charts.
// Run: node evals/charts/logo.mjs
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
import rough from "roughjs/bundled/rough.esm.js";

const here = path.dirname(fileURLToPath(import.meta.url));
const root = path.resolve(here, "..", "..");
const font = fs.readFileSync(path.join(here, "node_modules/@fontsource/caveat/files/caveat-latin-600-normal.woff2")).toString("base64");
const gen = rough.generator();
let seed = 7;

function paths(drawable, cls) {
  // Class by rough's set type: outline -> -l, hachure/zigzag strokes -> -h, solid fill -> -f.
  const kind = { path: "l", fillSketch: "h", fillPath: "f" };
  return gen.toPaths(drawable).map((p, i) => {
    const c = `${cls}-${kind[drawable.sets[i].type] || "l"}`;
    return `<path d="${p.d.replace(/(\d+\.\d)\d+/g, "$1")}" class="${c}" stroke-width="${p.strokeWidth}"/>`;
  }).join("");
}
const o = (extra) => ({ seed: seed++, stroke: "#000", fill: "#000", ...extra });

const parts = [];
// Slop: a lumpy puddle with drips and a couple of stink lines.
const blob = "M60 120 C 50 80, 95 62, 120 78 C 140 55, 185 70, 180 100 C 205 112, 195 150, 165 150 C 150 168, 120 160, 108 152 C 80 165, 48 150, 60 120 Z";
parts.push(paths(gen.path(blob, o({ roughness: 2, bowing: 2, strokeWidth: 2, fillStyle: "zigzag", hachureGap: 5, fillWeight: 1.2, hachureAngle: 30 })), "slop"));
for (const [x, y, len] of [[82, 155, 22], [128, 158, 30], [168, 148, 16]]) {
  parts.push(paths(gen.line(x, y, x + 1, y + len, o({ roughness: 1.4, strokeWidth: 2.2 })), "slop"));
  parts.push(paths(gen.circle(x + 1, y + len + 4, 7, o({ roughness: 1, strokeWidth: 1.6, fillStyle: "solid" })), "slop"));
}
for (const x of [100, 125, 150]) {
  parts.push(paths(gen.curve([[x, 52], [x - 6, 42], [x + 4, 32], [x - 2, 20]], o({ roughness: 1.2, strokeWidth: 1.4, fill: undefined })), "slop"));
}
// Arrow from slop to gold, passing a small "check" box.
parts.push(paths(gen.curve([[205, 112], [260, 92], [330, 92], [378, 112]], o({ roughness: 1.3, strokeWidth: 2.4, fill: undefined })), "ink"));
parts.push(paths(gen.linearPath([[362, 98], [380, 113], [358, 122]], o({ roughness: 1.2, strokeWidth: 2.4, fill: undefined })), "ink"));
parts.push(paths(gen.rectangle(262, 58, 74, 30, o({ roughness: 1.4, strokeWidth: 1.6, fill: undefined })), "ink"));
// Gold bar: top face, front face, side face, then a tick stamped on the front.
const top = [[425, 82], [525, 82], [545, 104], [405, 104]];
const front = [[405, 104], [545, 104], [565, 160], [385, 160]];
parts.push(paths(gen.polygon(top, o({ roughness: 1.1, strokeWidth: 2, fillStyle: "solid" })), "gold2"));
parts.push(paths(gen.polygon(front, o({ roughness: 1.2, strokeWidth: 2.2, fillStyle: "solid" })), "gold3"));
parts.push(paths(gen.polygon(front, o({ roughness: 1.2, strokeWidth: 2.2, fillStyle: "hachure", hachureGap: 4, fillWeight: 1.4, hachureAngle: -40 })), "gold"));
parts.push(paths(gen.polygon(top, o({ roughness: 1.1, strokeWidth: 2, fill: undefined })), "goldEdge"));
parts.push(paths(gen.polygon(front, o({ roughness: 1.2, strokeWidth: 2.2, fill: undefined })), "goldEdge"));
parts.push(paths(gen.linearPath([[450, 132], [469, 149], [503, 116]], o({ roughness: 1, strokeWidth: 5, fill: undefined })), "tick"));
// Sparkles.
for (const [x, y, r] of [[580, 70, 12], [560, 40, 7], [395, 66, 8]]) {
  parts.push(paths(gen.line(x - r, y, x + r, y, o({ roughness: 0.8, strokeWidth: 2 })), "spark"));
  parts.push(paths(gen.line(x, y - r, x, y + r, o({ roughness: 0.8, strokeWidth: 2 })), "spark"));
}

const svg = `<svg xmlns="http://www.w3.org/2000/svg" width="640" height="250" viewBox="0 0 640 250" role="img" aria-label="slop-to-gold logo: a blob of slop, an arrow through a check, a gold bar with a tick">
<style>
@font-face{font-family:Caveat;font-weight:600;src:url(data:font/woff2;base64,${font}) format("woff2")}
path{fill:none}
.slop-l,.slop-h{stroke:#7d6a4a}.slop-f{fill:#7d6a4a;stroke:none}.ink-l{stroke:#3b3a37}.tick-l{stroke:#5c3d00}
.gold-h{stroke:#e0a526}.gold2-f{fill:#f6d77a;stroke:none}.gold3-f{fill:#fbe9b0;stroke:none}.goldEdge-l{stroke:#9a6b0a}.spark-l{stroke:#e0a526}
text{font-family:Caveat,"Comic Sans MS",cursive}
.w{font-size:54px;fill:#1f1e1c}.ws{fill:#7d6a4a}.wg{fill:#c48a12}.c{font-size:22px;fill:#3b3a37}
@media (prefers-color-scheme: dark){
.slop-l,.slop-h{stroke:#b8a27a}.slop-f{fill:#b8a27a}.ink-l{stroke:#d6d4cc}.c{fill:#d6d4cc}.w{fill:#f0efec}.ws{fill:#b8a27a}.wg{fill:#f0b93a}
}
</style>
${parts.join("\n")}
<text x="299" y="80" class="c" text-anchor="middle">lint</text>
<text x="320" y="228" class="w" text-anchor="middle"><tspan class="ws">slop</tspan>-to-<tspan class="wg">gold</tspan></text>
</svg>`;
fs.writeFileSync(path.join(root, "docs", "logo.svg"), svg);
console.log("drew docs/logo.svg", svg.length, "bytes");
