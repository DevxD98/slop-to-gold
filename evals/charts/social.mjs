// Build docs/social-preview.svg (1280x640, light only) from docs/logo.svg for GitHub's
// social preview. Convert to PNG with any SVG renderer that loads @font-face, then upload it
// in Settings > Social preview.
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
import rough from "roughjs/bundled/rough.esm.js";

const here = path.dirname(fileURLToPath(import.meta.url));
const root = path.resolve(here, "..", "..");
const logo = fs.readFileSync(path.join(root, "docs", "logo.svg"), "utf8");
const style = logo.match(/<style>([\s\S]*?)<\/style>/)[1].replace(/@media[\s\S]*$/, "");
const body = logo.slice(logo.indexOf("</style>") + 8, logo.lastIndexOf("</svg>"));

const gen = rough.generator();
const frame = gen.toPaths(gen.rectangle(24, 24, 1232, 592, { seed: 3, roughness: 1.8, bowing: 2, stroke: "#000", strokeWidth: 2.4 }))
  .map((p) => `<path d="${p.d.replace(/(\d+\.\d)\d+/g, "$1")}" class="ink-l" stroke-width="2.4"/>`).join("");

const svg = `<svg xmlns="http://www.w3.org/2000/svg" width="1280" height="640" viewBox="0 0 1280 640">
<style>${style}.tag{font-size:44px;fill:#3b3a37}.url{font-size:30px;fill:#7d6a4a}</style>
<rect width="1280" height="640" fill="#fdf9ef"/>${frame}
<g transform="translate(160 40) scale(1.5)">${body}</g>
<text x="640" y="490" class="tag" text-anchor="middle">Turn repeated agent corrections into lint rules, types and tests,</text>
<text x="640" y="544" class="tag" text-anchor="middle">so the same AI slop can't come back.</text>
<text x="640" y="596" class="url" text-anchor="middle">a Claude Code skill · github.com/DevxD98/slop-to-gold</text>
</svg>`;
fs.writeFileSync(path.join(root, "docs", "social-preview.svg"), svg);

// Square plugin icon: just the gold bar and sparkles, on the same cream card.
const bar = body.replace(/<text[\s\S]*?<\/text>/g, "").replace(/<path[^>]*class="(ink|slop)-[a-z]"[^>]*\/>/g, "");
fs.writeFileSync(path.join(root, ".claude-plugin", "icon.svg"), `<svg xmlns="http://www.w3.org/2000/svg" width="512" height="512" viewBox="365 -12 240 240">
<style>${style}</style><rect x="365" y="-12" width="240" height="240" rx="36" fill="#fdf9ef"/>${bar}</svg>`);
console.log("drew docs/social-preview.svg");
