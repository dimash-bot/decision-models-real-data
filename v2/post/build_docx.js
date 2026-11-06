// Builds the Reddit post as a Word document with the charts from img/.
// Run: NODE_PATH=<dir with docx> node build_docx.js
const fs = require("fs");
const path = require("path");
const {
  Document, Packer, Paragraph, TextRun, HeadingLevel, ImageRun, Table, TableRow, TableCell, WidthType,
  ShadingType, BorderStyle, AlignmentType, LevelFormat, ExternalHyperlink, PageBreak,
} = require("docx");

const IMG = path.join(__dirname, "img");
const OUT = path.join(__dirname, "decision-models-reddit-post.docx");
const REPO = "https://github.com/dimash-bot/decision-models-real-data";
const FONT = "Arial", INK = "15191D", MUTED = "5B6670", ACCENT = "0F6F6A", WARN = "9A4B12", LINE = "D9DEE3";
const CONTENT_W = 9026; // A4 width minus two 1-inch margins, in DXA

// ---------- helpers
const run = (text, o = {}) => new TextRun({ text, font: FONT, size: o.size || 22, bold: !!o.bold, italics: !!o.italics, color: o.color || INK });
function para(parts, o = {}) {
  const children = (Array.isArray(parts) ? parts : [parts]).map(p => typeof p === "string" ? run(p, o) : p);
  return new Paragraph({ style: "Normal", children, spacing: { after: o.after ?? 140, line: 300 }, alignment: o.align, ...(o.border ? { border: o.border } : {}), ...(o.shade ? { shading: { type: ShadingType.CLEAR, fill: o.shade, color: "auto" } } : {}), indent: o.indent });
}
const rich = (s, o = {}) => s.split(/(\*\*[^*]+\*\*)/).filter(Boolean).map(t => t.startsWith("**") ? run(t.slice(2, -2), { ...o, bold: true }) : run(t, o));
const p = (s, o) => para(rich(s, o), o);
const h1 = (t, newPage) => new Paragraph({ heading: HeadingLevel.HEADING_1, pageBreakBefore: !!newPage, children: [new TextRun({ text: t })] });
const h2 = (t, newPage) => new Paragraph({ heading: HeadingLevel.HEADING_2, pageBreakBefore: !!newPage, children: [new TextRun({ text: t })] });
const bullet = s => new Paragraph({ numbering: { reference: "bul", level: 0 }, children: rich(s), spacing: { after: 80, line: 290 } });
const caption = s => para([run(s, { size: 18, italics: true, color: MUTED })], { after: 240 });
function image(file, alt) {
  const buf = fs.readFileSync(path.join(IMG, file));
  const w = buf.readUInt32BE(16), h = buf.readUInt32BE(20); // PNG IHDR
  const width = 600;
  return new Paragraph({ alignment: AlignmentType.CENTER, keepNext: true, keepLines: true, spacing: { before: 120, after: 60 },
    children: [new ImageRun({ type: "png", data: buf, transformation: { width, height: Math.round(width * h / w) }, altText: { title: alt, description: alt, name: file } })] });
}
const border = { style: BorderStyle.SINGLE, size: 4, color: LINE };
function table(header, rows, widths, o = {}) {
  const total = widths.reduce((a, b) => a + b, 0);
  const cell = (text, i, isHead, fill) => new TableCell({
    width: { size: widths[i], type: WidthType.DXA },
    margins: { top: 60, bottom: 60, left: 90, right: 90 },
    borders: { top: border, bottom: border, left: border, right: border },
    shading: { type: ShadingType.CLEAR, color: "auto", fill: isHead ? "EEF1F3" : (fill || "FFFFFF") },
    children: [new Paragraph({ spacing: { after: 0, line: 260 }, alignment: o.right && o.right.includes(i) && !isHead ? AlignmentType.RIGHT : AlignmentType.LEFT,
      children: rich(String(text), { size: 18, bold: isHead, color: isHead ? MUTED : INK }) })],
  });
  return new Table({
    width: { size: total, type: WidthType.DXA }, columnWidths: widths,
    rows: [new TableRow({ tableHeader: true, children: header.map((t, i) => cell(t, i, true)) }),
      ...rows.map(r => new TableRow({ children: r.cells.map((t, i) => cell(t, i, false, r.fill)) }))],
  });
}
const gap = () => para([run("")], { after: 120 });

// ---------- content (v3: reviewer comments applied; Drex Max v1.1 tested on Nace's own API)
const two = (a, b) => `${a} • ${b}`;
const VERDICT = [
  { fill: "DDF0EE", cells: ["**Perplexity Decider V1.2**", "**Use: best overall pick**", two("Tied #1 on accuracy (65.6%) at the lowest price of the top three ($0.018 per 1k).", "Open Apache-2.0 weights; doesn't train on or keep your prompts.")] },
  { fill: "DDF0EE", cells: ["**Nace Drex Max v1.1**", "**Use: strong second pick**", two("Tied #1 on accuracy (65.6%); top score on bug-vs-feature and Firefox components.", "Second most honest confidence; 95% of answers in under 0.9 s.")] },
  { fill: "DDF0EE", cells: ["**Liquid d1-ultra**", "**Use if accuracy matters most**", two("Highest accuracy (66.1%, tied) and the most honest confidence.", "Slowest 5% of requests took over 5 s; ~1.8% timed out on the first try.")] },
  { cells: ["**Liquid d1.1**", "**Use for cheap volume**", two("Cheapest ($0.016 per 1k) and fastest.", "Less accurate (63.7%) and least consistent on repeated questions (90.7%).")] },
  { fill: "FBEFE3", cells: ["**TypeSafe Jev 1.14**", "**Skip unless you already use it**", two("Mid-pack accuracy (64.2%) at nearly 3x Decider's price.", "Overconfident: 11.5 points more confident than accurate.")] },
  { fill: "FBEFE3", cells: ["**TypeSafe Jev 1.13**", "**Skip**", two("Same accuracy and price as 1.14.", "Older; if you're on Jev, use 1.14.")] },
  { fill: "F6DCDC", cells: ["**GPT-6 Luna Decisions**", "**Ignore**", two("Last on accuracy (62.8%) and most expensive ($0.091 per 1k).", "Most overconfident (+21 points) and keeps your prompts.")] },
];

const doc = new Document({
  creator: "Dimash",
  title: "Seven decision models on 2,826 real tech decisions",
  styles: {
    default: {
      document: { run: { font: FONT, size: 22, color: INK, bold: false } },
      title: { run: { font: FONT, size: 40, bold: true, color: INK }, paragraph: { spacing: { before: 0, after: 160 }, keepNext: true } },
      heading1: { run: { font: FONT, size: 30, bold: true, color: INK }, paragraph: { spacing: { before: 360, after: 140 }, keepNext: true } },
      heading2: { run: { font: FONT, size: 24, bold: true, color: ACCENT }, paragraph: { spacing: { before: 240, after: 100 }, keepNext: true } },
    },
    paragraphStyles: [
      { id: "Normal", name: "Normal", quickFormat: true, run: { font: FONT, size: 22, color: INK, bold: false, italics: false }, paragraph: { spacing: { before: 0, after: 140 } } },
    ],
  },
  numbering: { config: [{ reference: "bul", levels: [{ level: 0, format: LevelFormat.BULLET, text: "•", alignment: AlignmentType.LEFT, style: { paragraph: { indent: { left: 540, hanging: 270 } } } }] }] },
  sections: [{
    properties: { page: { margin: { top: 1440, bottom: 1440, left: 1440, right: 1440 } } },
    children: [
      new Paragraph({ heading: HeadingLevel.TITLE, children: [new TextRun({ text: "I tested 7 decision models on 2,826 real GitHub, Firefox and CVE decisions. Here's which one to use and which to skip." })] }),
      para([run("Reddit post draft · data through Nov 6, 2026", { size: 18, color: MUTED })], { after: 200 }),
      p("**Disclosure first:** I work at Nace.AI, which makes Drex Max, one of the models tested. The method, prompts and scoring formula were written down and checksummed before any model was run, every model got the same items and questions, and all data, raw outputs and code are public so you can re-score it yourself.",
        { shade: "FBEFE3", border: { left: { style: BorderStyle.SINGLE, size: 18, color: WARN, space: 8 } }, indent: { left: 120, right: 120 }, after: 240 }),

      h1("Summary: which decision model is best?"),
      p("**Short answer: Perplexity Decider V1.2 is the best overall pick, Nace Drex Max v1.1 is a strong second, and GPT-6 Luna Decisions is the one to ignore.** On accuracy alone Liquid d1-ultra, Drex Max and Decider are statistically tied; Decider wins on price and openness."),
      table(["Model", "Verdict", "Two facts"], VERDICT, [2000, 2100, 4926]),

      h1("What I tested"),
      p("Decision models don't write text. You give them some input and a typed question (yes/no, pick one, or a score), and they return a probability for every option in one pass. Seven models: **TypeSafe Jev 1.14 and 1.13, Perplexity Decider V1.2, Liquid d1-ultra and d1.1, OpenAI GPT-6 Luna Decisions, and Nace Drex Max v1.1.**"),
      h2("The data: real decisions, made after the models were released"),
      p("Every item was created after Sep 15, 2026, after the models were released, so none of it can be in their training data. The \"right answer\" is what the project's own maintainers actually decided."),
      table(["Task", "Source", "Items", "Question"], [
        { cells: ["T1", "VS Code + Kubernetes issues", "547", "Bug report or feature request?"] },
        { cells: ["T2", "VS Code, Next.js, TypeScript PRs", "472", "Will it be merged?"] },
        { cells: ["T3", "Firefox bugs (Bugzilla)", "534", "Which of 39 components owns it?"] },
        { cells: ["T4", "Firefox bugs (Bugzilla)", "292", "Severity S4 to S1?"] },
        { cells: ["T5", "GitHub security advisories", "479", "Severity low to critical?"] },
        { cells: ["T6", "NVD CVE feed (ready-made public dataset)", "500", "Which of 20 weakness types (CWE)?"] },
      ], [900, 3400, 900, 3826], { right: [2] }),
      gap(),
      h2("How I kept it fair"),
      bullet("**Same items and questions for every model.** Each model was called through its provider's API; Drex Max v1.1 through Nace's own API."),
      bullet("**No giveaways.** Labels, issue-template markers, CVSS scores, CWE numbers and the PR author's role were stripped from the text."),
      bullet("**Official option wording.** Bugzilla's component descriptions, Mozilla's severity scale, GitHub's advisory scale and MITRE's CWE definitions, not text I wrote."),
      bullet("**Three phrasings per question,** averaged, so no model wins because of my wording."),
      bullet("**Balanced classes, balanced accuracy, real statistics:** 95% bootstrap intervals and Holm-corrected pairwise tests across all 21 model pairs."),

      h1("Results"),
      h2("1. Accuracy: three models tied at the top"),
      image("1_accuracy.png", "Overall balanced accuracy with 95% intervals"),
      caption("Mean of balanced accuracy over the six tasks. Whiskers are 95% bootstrap intervals; the shaded group is statistically tied for #1."),
      p("d1-ultra (66.1%), Drex Max v1.1 (65.6%) and Decider (65.6%) overlap, so none of them is a clear winner. The gaps that are real: all three beat GPT-6 Luna and d1.1; d1-ultra also beats both Jev versions."),

      h2("2. Who leads which task"),
      image("2_tasks.png", "Balanced accuracy by task heatmap"),
      caption("Darker is better within each column. Bold is the column leader; outlined cells are statistically tied with it."),
      bullet("**Bug or feature:** everyone scores 90-93%. Drex Max is nominally first; all seven are tied."),
      bullet("**PR merged?** the hardest task. d1-ultra leads (63.6%), tied with Drex Max and Decider."),
      bullet("**Firefox component (39 choices):** Drex Max scores highest (77.8%), statistically tied with Decider, d1-ultra and Luna."),
      bullet("**Severity (Firefox and advisories):** everyone is in the 38-47% range and mostly tied; it's a hard call even for triagers."),
      bullet("**CVE weakness type:** Decider leads (76.0%); all seven are statistically tied."),

      h2("3. Value: accuracy per dollar"),
      image("3_value.png", "Accuracy versus cost per thousand decisions"),
      caption("Cost per 1,000 decisions at each provider's own price, on a log scale."),
      p("Decider is the best value: near-top accuracy at $0.018 per 1,000 decisions. Drex Max ($0.027 at $0.03 per 1M tokens) and d1-ultra ($0.034) cost a little more for the same tier of accuracy. d1.1 is the cheapest ($0.016) but less accurate. Jev ($0.051) and GPT-6 Luna ($0.091) cost the most for the lowest accuracy."),

      h2("4. How honest is each model's confidence?"),
      image("4_confidence.png", "Average confidence versus share of answers right"),
      caption("Average confidence in the chosen answer vs how often that answer was right, across all tasks. The gap is overconfidence."),
      p("A decision model is only useful if you can trust its probabilities. **d1-ultra (+1.7 points) and Drex Max (+4.6) are the most honest;** Decider and d1.1 are close behind (+6.1). Jev is about 12 points more confident than it is right, and **GPT-6 Luna is 21 points overconfident:** it says 87% on average and is right 66% of the time."),

      h2("5. Speed and consistency"),
      table(["Model", "Median latency", "Slowest 5%", "Same answer when repeated"], [
        { cells: ["Liquid d1.1", "632 ms", "746 ms", "90.7%"] },
        { cells: ["Nace Drex Max v1.1", "656 ms", "833 ms", "99.3%"] },
        { cells: ["TypeSafe Jev 1.14", "678 ms", "756 ms", "99.2%"] },
        { cells: ["Liquid d1-ultra", "682 ms", "**5,139 ms**", "95.7%"] },
        { cells: ["TypeSafe Jev 1.13", "699 ms", "885 ms", "97.3%"] },
        { cells: ["GPT-6 Luna Decisions", "758 ms", "1,078 ms", "100%"] },
        { cells: ["Perplexity Decider V1.2", "784 ms", "1,318 ms", "99.3%"] },
      ], [3000, 1900, 1900, 2226], { right: [1, 2, 3] }),
      gap(),

      h1("Total score: accuracy plus everything else"),
      p("I also scored five \"pillars\" from 0 to 100 and combined them with weights fixed before the run:"),
      bullet("**Quality (45%):** accuracy above chance, plus how good the probabilities are."),
      bullet("**Efficiency (20%):** cost per 1,000 decisions at the provider's own price, and median speed."),
      bullet("**Trust (20%):** does the provider train on or keep your prompts, is zero-data-retention available, are the weights and licence published, plus reliability and consistency in this run."),
      bullet("**Reviews (10%):** usage, plus Hacker News comments since September labelled by a model that isn't in the comparison."),
      bullet("**Signup bonus (5%):** free credit for a new account (Nace $5, Liquid $2, others none)."),
      image("5_total.png", "Total score broken down by pillar"),
      caption("Each segment is a pillar's score times its weight; the number is the total out of 100."),
      p("**Perplexity Decider is #1 (59.2),** mainly on trust: open weights, no prompt retention, zero-data-retention. **Drex Max v1.1 is #2 (53.0),** close to Decider on quality and efficiency; its trust score is lower because v1.1's weights aren't published and Nace's terms don't say clearly whether standard mode keeps request data. d1-ultra is #3 (49.7) and GPT-6 Luna last (39.1)."),

      h1("Pricing, openness and data policy"),
      table(["Model", "$ per 1M input", "Weights", "Licence", "Trains on prompts", "Keeps prompts", "Zero retention"], [
        { cells: ["Perplexity Decider V1.2", "0.019-0.020", "Yes", "Apache-2.0", "No", "No", "Yes"] },
        { cells: ["Liquid d1.1", "0.020", "No*", "-", "Conflicting", "Conflicting", "Yes"] },
        { cells: ["Nace Drex Max v1.1", "0.030", "No**", "-", "No", "Unclear", "Yes"] },
        { cells: ["Liquid d1-ultra", "0.042", "No*", "-", "Conflicting", "Conflicting", "Yes"] },
        { cells: ["TypeSafe Jev 1.13 / 1.14", "0.042", "No", "-", "No", "No", "Yes"] },
        { cells: ["GPT-6 Luna Decisions", "0.10", "No", "-", "No", "Yes", "No"] },
      ], [2050, 1350, 950, 1300, 1150, 1150, 1076]),
      para([run("Prices are each provider's own list price; output tokens are free for every model. * Smaller open relatives (d1-2B, d1-3B) exist, but not these models. ** Only the earlier drex-max-v1 is on Hugging Face (Open RAIL-M licence). Data policy: provider records on OpenRouter for the six OpenRouter models, Nace's terms for Drex Max.", { size: 18, color: MUTED })], { after: 160 }),

      h1("Limitations"),
      bullet("English, software-engineering text only. No images, no finance or legal text."),
      bullet("Labels are human decisions and contain mistakes: on 385 items all seven models agree with each other but not with the label. They're published for anyone to audit."),
      bullet("Drex Max v1.1 was called through Nace's API and the other six through OpenRouter, so latency also reflects the host."),
      bullet("Two items were dropped for every model: one advisory whose text contains an embedded image that Nace's API rejects, and one that d1-ultra never answered."),
      bullet("Prices, uptime and usage are a snapshot from Nov 6, 2026."),

      h1("Code, data and raw outputs"),
      para([run("Everything (pre-registration with checksums, all items, every raw model answer, and the code to re-score without an API key): ", {}),
        new ExternalHyperlink({ link: REPO, children: [new TextRun({ text: REPO, font: FONT, size: 22, color: ACCENT, underline: {} })] })]),
    ],
  }],
});

Packer.toBuffer(doc).then(b => { fs.writeFileSync(OUT, b); console.log("wrote", OUT, b.length, "bytes"); });
