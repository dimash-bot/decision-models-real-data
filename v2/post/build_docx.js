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
const h1 = t => new Paragraph({ heading: HeadingLevel.HEADING_1, children: [new TextRun({ text: t })] });
const h2 = t => new Paragraph({ heading: HeadingLevel.HEADING_2, children: [new TextRun({ text: t })] });
const bullet = s => new Paragraph({ numbering: { reference: "bul", level: 0 }, children: rich(s), spacing: { after: 80, line: 290 } });
const caption = s => para([run(s, { size: 18, italics: true, color: MUTED })], { after: 240 });
function image(file, alt) {
  const buf = fs.readFileSync(path.join(IMG, file));
  const w = buf.readUInt32BE(16), h = buf.readUInt32BE(20); // PNG IHDR
  const width = 600;
  return new Paragraph({ alignment: AlignmentType.CENTER, spacing: { before: 120, after: 60 },
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

// ---------- content
const VERDICT = [
  { fill: "DDF0EE", cells: ["**Perplexity Decider V1.2**", "**Use: best overall pick**", "Tied #1 on accuracy (65.6%), second cheapest ($0.018 per 1k), open Apache-2.0 weights, no training on or retention of prompts. #1 on the total score."] },
  { fill: "DDF0EE", cells: ["**Liquid d1-ultra**", "**Use if accuracy is everything**", "Highest accuracy (66.1%, tied) and best-calibrated probabilities. But its slowest 5% of requests took 5.1 s, ~1.8% of first attempts timed out, and OpenRouter's records on its data policy contradict each other."] },
  { cells: ["**Nace Drex Max**", "**Consider**", "Tied #1 on accuracy (64.9%) and best at bug-vs-feature. But it costs 3x Decider, its $0.06 price is a 50%-off promotion, and it is overconfident on PR merges."] },
  { cells: ["**Liquid d1.1**", "**Use for cheap, high volume**", "Cheapest ($0.016 per 1k) and fastest. Slightly less accurate (63.7%) and the least consistent: the same question gave the same answer only 90.7% of the time."] },
  { fill: "FBEFE3", cells: ["**TypeSafe Jev 1.14**", "**Skip unless you already use it**", "Mid-pack accuracy (64.2%), priced like Drex Max, and overconfident on severity (claims 90%+ and is right ~64%). Most popular by usage, but usage isn't accuracy."] },
  { fill: "FBEFE3", cells: ["**TypeSafe Jev 1.13**", "**Skip**", "Same accuracy and price as 1.14 and older. If you use Jev, use 1.14."] },
  { fill: "F6DCDC", cells: ["**GPT-6 Luna Decisions**", "**Ignore**", "Last on accuracy (62.8%), most expensive ($0.091 per 1k), most overconfident (claims 90%+ on 61% of severity answers and is right 46% of the time), keeps prompts, no zero-data-retention option on OpenRouter."] },
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
      p("**Disclosure first:** I work at Nace.AI, which makes Drex Max, one of the models tested. To keep that from tilting anything, the method, prompts and scoring formula were written down and checksummed before any model was run; every model got identical inputs through OpenRouter; pricing and openness come only from OpenRouter and Hugging Face, not from any company's marketing (Nace's included). All data, raw outputs and code are public, so you can re-score it yourself.",
        { shade: "FBEFE3", border: { left: { style: BorderStyle.SINGLE, size: 18, color: WARN, space: 8 } }, indent: { left: 120, right: 120 }, after: 240 }),

      h1("Summary: which decision model is best?"),
      p("**Short answer: Perplexity Decider V1.2 is the best overall pick, and GPT-6 Luna Decisions is the one to ignore.** On accuracy alone there is no single winner: Liquid d1-ultra, Perplexity Decider and Nace Drex Max are statistically tied. Decider wins on value: it matches the leaders' accuracy at a third of Drex Max's price, publishes its weights under Apache-2.0, and doesn't train on or keep your prompts."),
      table(["Model", "Verdict", "Why"], VERDICT, [2000, 2100, 4926]),
      gap(),
      p("**If you only read one thing:** use Decider by default; use d1-ultra if you need every last point of accuracy and can live with latency spikes; use d1.1 when cost matters more than the last 2 points of accuracy; don't use GPT-6 Luna Decisions."),

      h1("What I tested"),
      p("Decision models don't write text. You give them some input (the \"state\") and a typed question (yes/no, pick one, or a score), and they return a probability for every option in one pass. Seven models were tested through OpenRouter: **TypeSafe Jev 1.14 and 1.13, Perplexity Decider V1.2, Liquid d1-ultra and d1.1, OpenAI GPT-6 Luna Decisions, and Nace Drex Max.**"),
      h2("The data: real decisions, made after the models were released"),
      p("Every item was created after Sep 15, 2026, after all seven models were released, so none of it can be in their training data. The \"right answer\" is what the project's own maintainers actually decided."),
      table(["Task", "Source", "Items", "Question"], [
        { cells: ["T1", "VS Code + Kubernetes issues", "547", "Bug report or feature request?"] },
        { cells: ["T2", "VS Code, Next.js, TypeScript PRs", "472", "Will it be merged?"] },
        { cells: ["T3", "Firefox bugs (Bugzilla)", "534", "Which of 39 components owns it?"] },
        { cells: ["T4", "Firefox bugs (Bugzilla)", "292", "Severity S4 to S1?"] },
        { cells: ["T5", "GitHub security advisories", "480", "Severity low to critical?"] },
        { cells: ["T6", "NVD CVE feed (ready-made public dataset)", "500", "Which of 20 weakness types (CWE)?"] },
      ], [900, 3400, 900, 3826], { right: [2] }),
      gap(),
      h2("How I kept it fair"),
      bullet("**Same input for everyone.** Identical questions and items for all seven models, all called through OpenRouter."),
      bullet("**No giveaways.** Labels, issue-template markers, CVSS scores, CWE numbers and the PR author's role were stripped from the text."),
      bullet("**Official option wording.** Bugzilla's own component descriptions, Mozilla's severity scale, GitHub's advisory scale and MITRE's CWE definitions, not text I wrote."),
      bullet("**Three phrasings per question,** averaged, so no model wins because of my wording."),
      bullet("**Balanced classes and balanced accuracy,** so always guessing the common answer scores no better than chance."),
      bullet("**Real statistics.** 95% bootstrap intervals and pairwise tests with Holm correction across all 21 model pairs. A model is only called \"best\" if it beats #2 after that correction."),
      bullet("**Fixed in advance.** The method and scoring were checksummed before the first API call. 63,546 calls in total, about $3."),

      new Paragraph({ children: [new PageBreak()] }),
      h1("Results"),
      h2("1. Accuracy: three models tied at the top"),
      image("1_accuracy.png", "Overall balanced accuracy with 95% intervals"),
      caption("Mean of balanced accuracy over the six tasks. Whiskers are 95% bootstrap intervals; the shaded group is statistically tied for #1."),
      p("d1-ultra (66.1%), Decider (65.6%) and Drex Max (64.9%) overlap, so none of them is a clear winner. The gaps that are real: all three beat GPT-6 Luna; d1-ultra also beats both Jev versions and d1.1; Decider also beats d1.1."),

      h2("2. Who leads which task"),
      image("2_tasks.png", "Balanced accuracy by task heatmap"),
      caption("Darker is better within each column. Bold is the column leader; outlined cells are statistically tied with it."),
      bullet("**Bug or feature:** everyone scores 90-92%, so this is close to solved. Drex Max is nominally first; all seven are tied."),
      bullet("**PR merged?** the hardest task. d1-ultra leads (63.6%), tied with Decider and Drex Max. A one-line rule (\"is the author already part of the repo?\") scores 73.1%, better than every model. The models don't see that field, but it shows how much of this decision isn't in the text."),
      bullet("**Firefox component (39 choices):** Decider leads (77.6%). On bugs whose title doesn't name the component, all models drop by 3-5 points."),
      bullet("**Severity (Firefox and advisories):** everyone is in the 38-47% range and mostly tied. Triagers' own severity changed later on only 2.7% of bugs, so the labels are stable; this is just a hard call."),
      bullet("**CVE weakness type:** Decider (76.0%), Luna and Jev 1.13 are top. Many descriptions name the weakness (\"cross-site scripting\"), which makes parts of this easy."),

      new Paragraph({ children: [new PageBreak()] }),
      h2("3. Value: accuracy per dollar"),
      image("3_value.png", "Accuracy versus cost per thousand decisions"),
      caption("Cost is what OpenRouter actually billed in this run, on a log scale. The dashed circle is Drex Max at its list price."),
      p("Decider sits alone in the top-left: near-top accuracy at $0.018 per 1,000 decisions. d1.1 is the cheapest ($0.016) but less accurate. Drex Max ($0.055) and Jev ($0.051) cost about three times Decider for equal or lower accuracy, and Drex Max's price is a 50%-off promotion: at list price it would be the most expensive model here (about $0.11 per 1k). GPT-6 Luna ($0.091) is both the least accurate and, today, the most expensive."),

      h2("4. Can you trust a \"90% sure\"?"),
      image("4_overconfidence.png", "Accuracy when models claim 90 percent or more confidence"),
      caption("Severity tasks. A well-calibrated model that says 90%+ should be right at least 90% of the time."),
      p("This matters because the whole point of a decision model is that you threshold its probabilities. **GPT-6 Luna claims 90%+ on 61% of severity answers and is right only 46% of the time when it does.** Both Jev versions claim it on ~17% and are right ~64%. d1-ultra, Decider, Drex Max and d1.1 rarely claim 90%+ on severity, which is the honest behaviour on a hard task. One exception worth knowing: on PR merges, Drex Max claims 90%+ on 62% of answers and is right 67% of the time."),

      h2("5. Speed, reliability and consistency"),
      table(["Model", "Median latency", "Slowest 5%", "Errors after retries", "Same answer when repeated"], [
        { cells: ["Liquid d1.1", "632 ms", "746 ms", "0", "90.7%"] },
        { cells: ["TypeSafe Jev 1.14", "678 ms", "756 ms", "0", "99.2%"] },
        { cells: ["Liquid d1-ultra", "682 ms", "**5,139 ms**", "1 (~1.8% timed out first time)", "95.7%"] },
        { cells: ["TypeSafe Jev 1.13", "699 ms", "885 ms", "0", "97.3%"] },
        { cells: ["Nace Drex Max", "731 ms", "1,198 ms", "0", "97.3%"] },
        { cells: ["GPT-6 Luna Decisions", "758 ms", "1,078 ms", "0", "100%"] },
        { cells: ["Perplexity Decider V1.2", "784 ms", "1,318 ms", "0", "99.3%"] },
      ], [2500, 1450, 1450, 1900, 1726], { right: [1, 2, 3, 4] }),
      gap(),

      new Paragraph({ children: [new PageBreak()] }),
      h1("Total score: accuracy plus everything else"),
      p("Accuracy isn't the only thing that matters when you pick a provider, so I also scored five \"pillars\" from 0 to 100 and combined them with weights fixed before the run:"),
      bullet("**Quality (45%):** accuracy above chance, plus how good the probabilities are."),
      bullet("**Efficiency (20%):** billed cost per 1,000 decisions and median speed."),
      bullet("**Trust (20%):** does the provider train on or keep your prompts, is zero-data-retention available (per OpenRouter), are weights and licence published, plus reliability and consistency in this run."),
      bullet("**Reviews (10%):** OpenRouter usage, plus Hacker News comments since September, each labelled positive/neutral/negative by a model that isn't in the comparison. Models with fewer than 10 relevant comments get a neutral score."),
      bullet("**Signup bonus (5%):** free credit for a new account on the provider's own API (Nace $5, Liquid $2, others none)."),
      image("5_total.png", "Total score broken down by pillar"),
      caption("Each segment is a pillar's score times its weight. Example: Drex Max's red segment is its signup bonus adding 4.3 points; Decider has none."),
      p("**Perplexity Decider is #1 (59.2),** mainly because of its trust score (99.3: open weights, no prompt retention, zero-data-retention, very consistent). Drex Max is #2 (54.9), d1-ultra #3 (49.7), and GPT-6 Luna last (39.1)."),
      h2("Does the winner depend on the weights?"),
      image("6_random_weights.png", "Share of random weightings each model wins"),
      caption("10,000 random weightings of the pillars. Grey: all five pillars. Green: without the signup-bonus pillar."),
      p("Yes, partly, and this is the part to read carefully. With all five pillars, Drex Max wins more random weightings (47%) than Decider (33%), so by the rule I fixed in advance **no model is \"best overall\" on the total score.** But **Drex Max's wins come entirely from its $5 signup bonus:** remove that pillar and Decider wins 87% of weightings, Jev 1.13 12%, and Drex Max 0%. Signup bonuses also don't apply when you use these models through OpenRouter. That's why the summary recommends Decider."),

      h1("Pricing, openness and data policy"),
      p("Sources: OpenRouter's public model and endpoint records, Hugging Face metadata and licence files. No company's own marketing."),
      table(["Model", "$ per 1M input", "Weights", "Licence", "Trains on prompts", "Keeps prompts", "Zero retention"], [
        { cells: ["Perplexity Decider V1.2", "0.019-0.020", "Yes", "Apache-2.0", "No", "No", "Yes"] },
        { cells: ["Liquid d1.1", "0.020", "No*", "-", "Conflicting", "Conflicting", "Yes"] },
        { cells: ["Liquid d1-ultra", "0.042", "No*", "-", "Conflicting", "Conflicting", "Yes"] },
        { cells: ["TypeSafe Jev 1.13 / 1.14", "0.042", "No", "-", "No", "No", "Yes"] },
        { cells: ["Nace Drex Max", "0.06 (50% off; list 0.12)", "drex-max-v1", "Open RAIL-M**", "No", "No", "Yes"] },
        { cells: ["GPT-6 Luna Decisions", "0.10", "No", "-", "No", "Yes", "No"] },
      ], [1900, 1450, 1000, 1300, 1150, 1150, 1076]),
      para([run("* Smaller open relatives (d1-2B, d1-3B) exist, but not the served models. ** Commercial licence needed for organisations with more than $1M revenue or funding. Output tokens are free for every model.", { size: 18, color: MUTED })], { after: 160 }),
      p("One observation, not a conclusion: Hugging Face lists exactly the same parameter count (26,085,330,160) for Drex Max and for Perplexity's Decider models, which name Qwen3.8-27B as their base. Drex Max's model card names no base model."),

      h1("Limitations"),
      bullet("English, software-engineering text only. No images, no finance or legal text."),
      bullet("Labels are human decisions and contain mistakes: on 381 items all seven models agree with each other but not with the label. They're published for anyone to audit."),
      bullet("Prices, uptime and usage are a snapshot from Nov 6, 2026. Drex Max's promotion could end at any time."),
      bullet("The reviews pillar is thin: only Jev and Luna had 10+ relevant Hacker News mentions."),
      bullet("Reliability in the trust score is measured after retries, as pre-registered, so d1-ultra's first-attempt timeouts are reported separately rather than penalised there."),

      h1("Code, data and raw outputs"),
      para([run("Everything (pre-registration with checksums, all 2,826 items, all 63,546 raw model answers, and the code to re-score without an API key): ", {}),
        new ExternalHyperlink({ link: REPO, children: [new TextRun({ text: REPO, font: FONT, size: 22, color: ACCENT, underline: {} })] })]),
    ],
  }],
});

Packer.toBuffer(doc).then(b => { fs.writeFileSync(OUT, b); console.log("wrote", OUT, b.length, "bytes"); });
