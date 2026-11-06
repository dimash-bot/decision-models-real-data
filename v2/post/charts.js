// Draws the post's charts from results.json / total_score.json into post/img/*.png.
// Run: NODE_PATH=<dir with @resvg/resvg-js> node charts.js
const fs = require("fs");
const path = require("path");
const { Resvg } = require("@resvg/resvg-js");

const V2 = path.join(__dirname, "..");
const R = JSON.parse(fs.readFileSync(path.join(V2, "results.json")));
const TS = JSON.parse(fs.readFileSync(path.join(V2, "total_score.json")));
const CONF = JSON.parse(fs.readFileSync(path.join(V2, "confidence.json")));
const OUT = path.join(__dirname, "img");
fs.mkdirSync(OUT, { recursive: true });

const NAME = {
  "liquid/d1-ultra": "Liquid d1-ultra", "perplexity/pplx-decider-v1.2": "Perplexity Decider V1.2",
  "nace-ai/drex-max": "Nace Drex Max v1.0", "nace-ai/drex-max-v1.1": "Nace Drex Max v1.1", "typesafe/jev-1.13": "TypeSafe Jev 1.13", "typesafe/jev-1.14": "TypeSafe Jev 1.14",
  "liquid/d1.1": "Liquid d1.1", "openai/gpt-6-luna-decisions": "GPT-6 Luna Decisions",
};
const C = { fg: "#15191d", muted: "#5b6670", line: "#d9dee3", grid: "#eceff2", accent: "#0f6f6a", soft: "#d7ecea", warn: "#b0413e", bg: "#ffffff" };
const SER = ["#0f6f6a", "#3e6fb5", "#7a4fae", "#a8790f", "#b0413e"];
const FONT = "Helvetica, Arial, sans-serif";
const esc = s => String(s).replace(/&/g, "&amp;").replace(/</g, "&lt;");
const tied = new Set(R.verdict.overall);
const models = [...R.models].sort((a, b) => R.point[b].overall - R.point[a].overall);

function save(name, W, H, body) {
  const svg = `<svg xmlns="http://www.w3.org/2000/svg" width="${W}" height="${H}" viewBox="0 0 ${W} ${H}" font-family="${FONT}">
<rect width="${W}" height="${H}" fill="${C.bg}"/>${body}</svg>`;
  const png = new Resvg(svg, { fitTo: { mode: "width", value: W * 2 }, font: { loadSystemFonts: true, defaultFontFamily: "Helvetica" } }).render().asPng();
  fs.writeFileSync(path.join(OUT, name + ".png"), png);
  console.log("wrote", name, W, "x", H);
}
const title = (t, sub) => `<text x="24" y="34" font-size="20" font-weight="700" fill="${C.fg}">${esc(t)}</text>` +
  (sub ? `<text x="24" y="56" font-size="13" fill="${C.muted}">${esc(sub)}</text>` : "");

// 1. Overall balanced accuracy with 95% CI
(function accuracy() {
  const W = 900, left = 230, right = 60, top = 84, rowH = 40, H = top + models.length * rowH + 50;
  const lo = 0.60, hi = 0.70, x = v => left + (v - lo) / (hi - lo) * (W - left - right);
  let s = title("Overall balanced accuracy (6 tasks, 3 phrasings each)", "Dot = score, whiskers = 95% bootstrap interval. Shaded = statistically tied for #1 (Holm-corrected).");
  const nt = models.filter(m => tied.has(m)).length;
  s += `<rect x="${left - 10}" y="${top}" width="${W - left - right + 20}" height="${nt * rowH}" fill="${C.soft}" rx="6"/>`;
  for (let v = 0.60; v <= 0.7001; v += 0.02) s += `<line x1="${x(v)}" x2="${x(v)}" y1="${top}" y2="${top + models.length * rowH}" stroke="${C.grid}"/><text x="${x(v)}" y="${top + models.length * rowH + 22}" font-size="12" fill="${C.muted}" text-anchor="middle">${Math.round(v * 100)}%</text>`;
  models.forEach((m, i) => {
    const y = top + i * rowH + rowH / 2, p = R.point[m].overall, [a, b] = R.ci[m].overall, col = tied.has(m) ? C.accent : C.muted;
    s += `<text x="${left - 18}" y="${y + 5}" font-size="14" fill="${C.fg}" text-anchor="end">${esc(NAME[m])}</text>`;
    s += `<line x1="${x(a)}" x2="${x(b)}" y1="${y}" y2="${y}" stroke="${col}" stroke-width="2.5"/>`;
    s += [a, b].map(v => `<line x1="${x(v)}" x2="${x(v)}" y1="${y - 7}" y2="${y + 7}" stroke="${col}" stroke-width="2.5"/>`).join("");
    s += `<circle cx="${x(p)}" cy="${y}" r="7" fill="${col}"/><text x="${x(b) + 10}" y="${y + 5}" font-size="13" fill="${C.fg}">${(p * 100).toFixed(1)}%</text>`;
  });
  save("1_accuracy", W, H, s);
})();

// 2. Per-task heatmap
(function heat() {
  const tasks = R.tasks, TN = { T1: "Bug vs\nfeature", T2: "PR\nmerged?", T3: "Firefox\ncomponent", T4: "Firefox\nseverity", T5: "Advisory\nseverity", T6: "CVE\nweakness" };
  const W = 900, left = 230, top = 110, cw = (W - left - 24) / tasks.length, rh = 40, H = top + models.length * rh + 40;
  let s = title("Balanced accuracy by task", "Darker = better within each column. Bold = column leader. Outlined = tied with the leader.");
  tasks.forEach((t, j) => {
    const [l1, l2] = TN[t].split("\n");
    s += `<text x="${left + j * cw + cw / 2}" y="${top - 30}" font-size="13" font-weight="700" fill="${C.fg}" text-anchor="middle">${l1}</text><text x="${left + j * cw + cw / 2}" y="${top - 13}" font-size="13" font-weight="700" fill="${C.fg}" text-anchor="middle">${l2}</text>`;
    const vals = models.map(m => R.point[m][t]), mn = Math.min(...vals), mx = Math.max(...vals), lead = R.verdict[t];
    models.forEach((m, i) => {
      const v = R.point[m][t], k = mx > mn ? (v - mn) / (mx - mn) : 1, a = 0.12 + 0.78 * k;
      const fill = `rgba(15,111,106,${a.toFixed(2)})`, txt = a > 0.55 ? "#ffffff" : C.fg, isLead = v === mx;
      s += `<rect x="${left + j * cw + 3}" y="${top + i * rh + 3}" width="${cw - 6}" height="${rh - 6}" rx="4" fill="${fill}" ${lead.includes(m) && !isLead ? `stroke="${C.fg}" stroke-width="1.5"` : ""}/>`;
      s += `<text x="${left + j * cw + cw / 2}" y="${top + i * rh + rh / 2 + 5}" font-size="13" ${isLead ? 'font-weight="700"' : ""} fill="${txt}" text-anchor="middle">${(v * 100).toFixed(1)}</text>`;
    });
  });
  models.forEach((m, i) => s += `<text x="${left - 14}" y="${top + i * rh + rh / 2 + 5}" font-size="14" fill="${C.fg}" text-anchor="end">${esc(NAME[m])}</text>`);
  save("2_tasks", W, H, s);
})();

// 3. Cost vs accuracy
(function value() {
  const W = 900, H = 520, L = 90, Rr = 40, T = 80, B = 70;
  const cmin = 0.01, cmax = 0.12, amin = 0.62, amax = 0.67;
  const x = c => L + Math.log(c / cmin) / Math.log(cmax / cmin) * (W - L - Rr), y = a => H - B - (a - amin) / (amax - amin) * (H - T - B);
  let s = title("Accuracy vs cost per 1,000 decisions", "Up and to the left is better. Cost at each provider's own price (log scale).");
  [0.01, 0.02, 0.05, 0.1].forEach(c => s += `<line x1="${x(c)}" x2="${x(c)}" y1="${T}" y2="${H - B}" stroke="${C.grid}"/><text x="${x(c)}" y="${H - B + 22}" font-size="12" fill="${C.muted}" text-anchor="middle">$${c.toFixed(2)}</text>`);
  for (let a = 0.62; a <= 0.6701; a += 0.01) s += `<line x1="${L}" x2="${W - Rr}" y1="${y(a)}" y2="${y(a)}" stroke="${C.grid}"/><text x="${L - 10}" y="${y(a) + 4}" font-size="12" fill="${C.muted}" text-anchor="end">${Math.round(a * 100)}%</text>`;
  s += `<text x="${(L + W - Rr) / 2}" y="${H - 22}" font-size="13" fill="${C.muted}" text-anchor="middle">Cost per 1,000 decisions</text>`;
  const off = { "typesafe/jev-1.13": [10, -10], "typesafe/jev-1.14": [10, 16], "nace-ai/drex-max-v1.1": [10, 20], "perplexity/pplx-decider-v1.2": [-12, 5, "end"], "openai/gpt-6-luna-decisions": [-12, 5, "end"] };
  models.forEach(m => {
    const cx = x(R.ops[m].cost_per_1k), cy = y(R.point[m].overall), col = tied.has(m) ? C.accent : C.muted, [dx, dy, anc] = off[m] || [10, 5];
    s += `<circle cx="${cx}" cy="${cy}" r="8" fill="${col}"/><text x="${cx + dx}" y="${cy + dy}" font-size="13" fill="${C.fg}" text-anchor="${anc || "start"}">${esc(NAME[m])}</text>`;
  });
  save("3_value", W, H, s);
})();

// 4. Average confidence vs share right (all tasks)
(function conf() {
  const order = Object.keys(CONF).sort((a, b) => CONF[a].gap - CONF[b].gap);
  const W = 900, left = 230, right = 120, top = 104, rowH = 42, H = top + order.length * rowH + 50;
  const lo = 0.60, hi = 0.90, x = v => left + (v - lo) / (hi - lo) * (W - left - right);
  let s = title("How honest is each model's confidence?", "Average confidence in its answer vs how often that answer was right, all tasks. Shorter bar = more honest.");
  s += `<circle cx="30" cy="78" r="6" fill="${C.fg}"/><text x="42" y="83" font-size="13" fill="${C.fg}">Share right</text>`;
  s += `<circle cx="150" cy="78" r="6" fill="none" stroke="${C.warn}" stroke-width="2.5"/><text x="162" y="83" font-size="13" fill="${C.fg}">Average confidence</text>`;
  for (let v = 0.60; v <= 0.9001; v += 0.05) s += `<line x1="${x(v)}" x2="${x(v)}" y1="${top}" y2="${top + order.length * rowH}" stroke="${C.grid}"/><text x="${x(v)}" y="${top + order.length * rowH + 22}" font-size="12" fill="${C.muted}" text-anchor="middle">${Math.round(v * 100)}%</text>`;
  order.forEach((m, i) => {
    const y = top + i * rowH + rowH / 2, c = CONF[m], gap = c.gap, col = gap > 0.1 ? C.warn : C.accent;
    s += `<text x="${left - 14}" y="${y + 5}" font-size="14" fill="${C.fg}" text-anchor="end">${esc(NAME[m])}</text>`;
    s += `<line x1="${x(c.accuracy)}" x2="${x(c.avg_confidence)}" y1="${y}" y2="${y}" stroke="${col}" stroke-width="6" stroke-linecap="round" opacity="0.35"/>`;
    s += `<circle cx="${x(c.accuracy)}" cy="${y}" r="7" fill="${C.fg}"/><circle cx="${x(c.avg_confidence)}" cy="${y}" r="7" fill="${C.bg}" stroke="${C.warn}" stroke-width="2.5"/>`;
    s += `<text x="${x(c.avg_confidence) + 14}" y="${y + 5}" font-size="13" font-weight="700" fill="${col}">+${(gap * 100).toFixed(1)} pts</text>`;
  });
  save("4_confidence", W, H, s);
})();

// 5. Total score stacked
(function total() {
  const order = Object.keys(TS.total).sort((a, b) => TS.total[b] - TS.total[a]);
  const keys = [["quality", .45, "Quality 45%"], ["efficiency", .20, "Efficiency 20%"], ["trust", .20, "Trust 20%"], ["reviews", .10, "Reviews 10%"], ["bonus", .05, "Signup bonus 5%"]];
  const W = 900, left = 230, right = 70, top = 104, rowH = 38, H = top + order.length * rowH + 50, max = 70, x = v => (W - left - right) * v / max;
  let s = title("Total score: where each model's points come from", "Segment = pillar score (0-100) x weight. Number = total out of 100.");
  let lx = 24;
  keys.forEach((k, i) => { s += `<rect x="${lx}" y="72" width="12" height="12" fill="${SER[i]}" rx="2"/><text x="${lx + 18}" y="83" font-size="13" fill="${C.fg}">${k[2]}</text>`; lx += 30 + k[2].length * 7.4; });
  for (let v = 0; v <= max; v += 10) s += `<line x1="${left + x(v)}" x2="${left + x(v)}" y1="${top}" y2="${top + order.length * rowH}" stroke="${C.grid}"/><text x="${left + x(v)}" y="${top + order.length * rowH + 22}" font-size="12" fill="${C.muted}" text-anchor="middle">${v}</text>`;
  order.forEach((m, i) => {
    const y = top + i * rowH + 8; let cx = left;
    s += `<text x="${left - 14}" y="${y + 16}" font-size="14" fill="${C.fg}" text-anchor="end">${esc(NAME[m])}</text>`;
    keys.forEach((k, j) => { const w = x(TS.pillars[m][k[0]] * k[1]); s += `<rect x="${cx}" y="${y}" width="${w}" height="22" fill="${SER[j]}"/>`; cx += w; });
    s += `<text x="${cx + 8}" y="${y + 16}" font-size="14" font-weight="700" fill="${C.fg}">${TS.total[m].toFixed(1)}</text>`;
  });
  save("5_total", W, H, s);
})();

// 6. Random-weight wins with and without the signup bonus
(function wins() {
  const noBonus = { "perplexity/pplx-decider-v1.2": .87, "typesafe/jev-1.13": .12, "liquid/d1.1": .01 };
  const order = Object.keys(TS.total).sort((a, b) => TS.total[b] - TS.total[a]);
  const W = 900, left = 230, top = 104, rowH = 40, H = top + order.length * rowH + 50, w = W - left - 80;
  let s = title("Who wins if you pick the weights at random?", "Share of 10,000 random weightings where each model is #1.");
  s += `<rect x="24" y="72" width="12" height="12" fill="#c9d3dc" rx="2"/><text x="42" y="83" font-size="13" fill="${C.fg}">All five pillars (pre-registered)</text>`;
  s += `<rect x="290" y="72" width="12" height="12" fill="${C.accent}" rx="2"/><text x="308" y="83" font-size="13" fill="${C.fg}">Without the signup-bonus pillar (exploratory)</text>`;
  [0, .25, .5, .75, 1].forEach(v => s += `<line x1="${left + v * w}" x2="${left + v * w}" y1="${top}" y2="${top + order.length * rowH}" stroke="${C.grid}"/><text x="${left + v * w}" y="${top + order.length * rowH + 22}" font-size="12" fill="${C.muted}" text-anchor="middle">${v * 100}%</text>`);
  order.forEach((m, i) => {
    const y = top + i * rowH + 6, a = TS.random_weight_wins[m], b = noBonus[m] || 0;
    s += `<text x="${left - 14}" y="${y + 18}" font-size="14" fill="${C.fg}" text-anchor="end">${esc(NAME[m])}</text>`;
    s += `<rect x="${left}" y="${y}" width="${Math.max(a * w, 1)}" height="13" fill="#c9d3dc"/><text x="${left + a * w + 6}" y="${y + 11}" font-size="12" fill="${C.muted}">${Math.round(a * 100)}%</text>`;
    s += `<rect x="${left}" y="${y + 15}" width="${Math.max(b * w, 1)}" height="13" fill="${C.accent}"/><text x="${left + b * w + 6}" y="${y + 26}" font-size="12" fill="${C.accent}">${Math.round(b * 100)}%</text>`;
  });
  save("6_random_weights", W, H, s);
})();
