// Builds the playbook page (artifact + repo copy) and the markdown docs from one data set.
import fs from "node:fs";
import path from "node:path";
import vm from "node:vm";

// Usage: node playbook/src/build.mjs [--url <published page link>] [--artifact <output path for the publishable page>]
const SRC = path.dirname(new URL(import.meta.url).pathname);
const REPO = path.resolve(SRC, "..", "..");
const arg = name => { const i = process.argv.indexOf(name); return i > -1 ? process.argv[i + 1] : ""; };
const PAGE_URL = arg("--url");
const ARTIFACT_OUT = arg("--artifact");
const read = f => fs.readFileSync(path.join(SRC, f), "utf8");

const ctx = {};
vm.createContext(ctx);
for (const f of ["opportunities-services.js", "opportunities-ai-products.js", "results-picks-platforms-rules.js", "plan-and-templates.js", "sources.js"]) {
  vm.runInContext(read(f) + "\n;globalThis.__x = 1;", ctx, {filename: f});
}
const get = name => vm.runInContext(name, ctx);

const CATS = {web:"Websites and apps", data:"Spreadsheets and data", docs:"Documents and writing", ai:"AI and automation", products:"Products you sell", results:"Paid on results"};
const opps = [...get("OPPS_WEB_DATA_DOCS"), ...get("OPPS_AI_PRODUCTS"), ...get("OPPS_RESULTS")].sort((a, b) => a.rank - b.rank);
// sanity checks
const ids = new Set();
for (const o of opps) {
  if (ids.has(o.id)) throw new Error("duplicate id " + o.id);
  ids.add(o.id);
  for (const k of ["cat","rank","zero","speed","fit","value","name","short","price","need","how","where","signal","risk","skill","gig"]) if (o[k] === undefined) throw new Error(o.id + " missing " + k);
  if (!CATS[o.cat]) throw new Error("bad cat " + o.cat);
}
const ranks = opps.map(o => o.rank);
if (new Set(ranks).size !== ranks.length) throw new Error("duplicate ranks");

const DATA = {
  cats: CATS, opps, picks: get("PICKS"), fees: get("FEES"), platformGroups: get("PLATFORM_GROUPS"),
  rulesDo: get("RULES_DO"), rulesDont: get("RULES_DONT"), plan: get("PLAN"), templates: get("TEMPLATES"),
  workspace: get("WORKSPACE"), sources: get("SOURCES")
};
const STAGES = get("STAGES"), PRINCIPLES = get("PRINCIPLES");
const nSources = DATA.sources.reduce((n, g) => n + g.items.length, 0);
const nPlatforms = DATA.platformGroups.reduce((n, g) => n + g.rows.length, 0);

const esc = s => String(s).replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;").replace(/"/g, "&quot;");

const copy = {
  __DATE__: "October 2026",
  __NSRC__: String(nSources),
  __LEDE__: "What people pay for that Claude can do well, where to find buyers when nobody knows you yet, and a 30-day plan to your first paid job. <strong>Ranked for someone starting from zero:</strong> no reviews, no portfolio, no network.",
  __META__: `<span><b>${opps.length}</b> ways to earn</span><span><b>${nPlatforms}</b> platforms compared</span><span><b>10</b> research passes</span><span>Prices in USD</span>`,
  __PICKS_SUB__: "Each pick either lets the buyer see the work before paying, or is small enough that buyers will take a chance on a newcomer. Do the first one this week; add others as you get reviews.",
  __REALITY_SUB__: "Claude makes the work fast. It doesn't bring clients and it doesn't make strangers trust you. The data is sobering. One dataset of Claude Code businesses that owners listed on a revenue tracker found fewer than half earned anything, and the typical one made about $145–227 a month. The ranges below are targets for someone who works the plan every week, not promises.",
  __STAGES__: STAGES.map(s => `<div class="stage"><div class="when">${esc(s.when)}</div><div class="amt">${esc(s.amt)}</div><p>${esc(s.text)}</p></div>`).join(""),
  __PRINCIPLES__: PRINCIPLES.map(p => `<li><b>${esc(p[0])}</b>${esc(p[1])}</li>`).join(""),
  __EXPLORE_SUB__: "Every option the research turned up, with prices, where buyers are, and how Claude does the work in this workspace. Open a row for details. \"No reviews needed\" means buyers judge the work or product itself; \"With samples\" means a newcomer can win with a portfolio and a low first price.",
  __WHERE_SUB__: "What each platform costs you and its rules on AI. Fees change, so check the platform before you rely on a number. The calculator shows what you keep after fees and your Claude plan.",
  __RULES_SUB__: "Anthropic's consumer terms allow you to sell work made with Claude. Most of the ways people get banned or burned come from the rules below, checked against Anthropic's own pages and each platform's policies.",
  __RULES_CALLOUT__: `<p class="callout"><b>Scam rule:</b> if someone wants money from you before you've earned anything, or wants to move you to Telegram or WhatsApp right away, walk away. The FTC reports record losses to \"pay to get paid\" job scams.</p><p class="callout"><b>Side income that needs no reviews, but no Claude either:</b> AI-training platforms such as DataAnnotation, Outlier and Mercor pay roughly $15–$60+ an hour if you pass their tests. They ban AI tools, and using Claude there also breaks Anthropic's usage policy, so this work has to be done by you personally.</p>`,
  __PLAN_SUB__: "Built for zero reviews. Your progress is saved in this browser only.",
  __TPL_SUB__: "Fill in the brackets, then make each one sound like you. They are also saved as files in the repo's templates folder.",
  __WS_SUB__: "How to run client work in Claude Code without losing files, leaking data or burning through your limits.",
  __SRC_SUB__: `${nSources} sources across 10 research passes, October 2026. This environment's network policy blocked most sites, so the research agents read most pages through search-result summaries; Anthropic's terms and policies were read directly. Prices and fees change, so check before you rely on them.`,
  __FOOTER__: "Research compiled with Claude Code in October 2026. Not legal, tax or financial advice. Every figure is from the linked sources or marked as an estimate."
};

let body = read("body.html");
for (const [k, v] of Object.entries(copy)) body = body.split(k).join(v);
const left = body.match(/__[A-Z_]+__/g);
if (left) throw new Error("unfilled placeholders: " + left.join(","));

const head = `<title>Claude Income Playbook</title>
<meta name="description" content="Ways to earn with Claude when you're starting from zero: services, products, platforms, rules and a 30-day plan.">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Archivo:wdth,wght@62..125,400..900&family=IBM+Plex+Mono:wght@400;500;600&family=Public+Sans:ital,wght@0,400..700;1,400..700&display=swap">
<style>
${read("style.css")}
</style>`;
const scripts = `<script>window.PLAYBOOK = ${JSON.stringify(DATA).replace(/</g, "\\u003c")};</script>
<script>
${read("app.js")}
</script>`;

// The publishable page has no <html>/<head>/<body>: the host wraps it in its own skeleton.
const artifact = `${head}\n${body}\n${scripts}\n`;
if (ARTIFACT_OUT) fs.writeFileSync(ARTIFACT_OUT, artifact);

// Full standalone document for the repo copy
const standalone = `<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
${head}
<style>[hidden]{display:none!important}body{margin:0}</style>
</head>
<body>
${body}
${scripts}
</body>
</html>
`;
fs.mkdirSync(path.join(REPO, "playbook"), {recursive: true});
fs.writeFileSync(path.join(REPO, "playbook", "index.html"), standalone);

// ---------- Markdown ----------
const md = s => String(s).replace(/<b>(.*?)<\/b>/g, "**$1**").replace(/<[^>]+>/g, "");
const cell = s => md(s).replace(/\|/g, "\\|").replace(/\n/g, " ");
const SPEED = {1:"Days", 2:"1–4 weeks", 3:"Months"};
const ZERO = {2:"Yes", 1:"With samples", 0:"Needs a track record"};
const L = [];
L.push("# Claude Income Playbook", "");
L.push("What people pay for that Claude can do well, where to find buyers when nobody knows you yet, and a 30-day plan to your first paid job. Ranked for someone starting from zero: no reviews, no portfolio, no network.", "");
if (PAGE_URL) L.push(`**Interactive version (filters, fee calculator, checklist):** ${PAGE_URL}`, "");
L.push(`Researched October 2026 · ${opps.length} ways to earn · ${nPlatforms} platforms · ${nSources} sources. Not legal, tax or financial advice.`, "");
L.push("## Contents", "", "1. [Start here](#start-here)", "2. [Reality check](#reality-check)", "3. [All opportunities](#all-opportunities)", "4. [Where to sell](#where-to-sell)", "5. [Rules](#rules)", "6. [30-day plan](#30-day-plan)", "7. [Templates](#templates)", "8. [Using this workspace](#using-this-workspace)", "9. [Sources](#sources)", "");
L.push("## Start here", "", md(copy.__PICKS_SUB__), "");
L.push("| # | Pick | Charge | First $ | Sell on |", "|---|---|---|---|---|");
DATA.picks.forEach((p, i) => L.push(`| ${i + 1} | **${cell(p.name)}**: ${cell(p.what)} ${cell(p.why)} | ${cell(p.price)} | ${cell(p.first)} | ${cell(p.where)} |`));
L.push("", "## Reality check", "", md(copy.__REALITY_SUB__), "");
STAGES.forEach(s => L.push(`- **${s.when}: ${s.amt}.** ${s.text}`));
L.push("");
PRINCIPLES.forEach(p => L.push(`- **${p[0]}** ${p[1]}`));
L.push("", "## All opportunities", "", md(copy.__EXPLORE_SUB__), "");
L.push("| Opportunity | Field | Typical price | First $ | No reviews needed? | Claude fit |", "|---|---|---|---|---|---|");
opps.forEach(o => L.push(`| [${cell(o.name)}](#${o.id}) | ${CATS[o.cat]} | ${cell(o.price)} | ${SPEED[o.speed]} | ${ZERO[o.zero]} | ${"●".repeat(o.fit)}${"○".repeat(3 - o.fit)} |`));
L.push("");
for (const cat of Object.keys(CATS)) {
  L.push(`### ${CATS[cat]}`, "");
  opps.filter(o => o.cat === cat).forEach(o => {
    L.push(`<a id="${o.id}"></a>`, `#### ${o.name}`, "", `*${o.short}.* **${o.price}** · first $ in ${SPEED[o.speed].toLowerCase()} · no reviews needed: ${ZERO[o.zero].toLowerCase()}`, "");
    L.push(`- **What buyers need:** ${md(o.need)}`, `- **How Claude does it here:** ${md(o.how)}`, `- **Where to find buyers:** ${md(o.where)}`, `- **Demand signal:** ${md(o.signal)}`, `- **Watch out:** ${md(o.risk)}`, `- **Skill needed from you:** ${md(o.skill)}`, `- **Example:** "${md(o.gig)}"`, "");
  });
}
L.push("## Where to sell", "", md(copy.__WHERE_SUB__), "");
DATA.platformGroups.forEach(g => {
  L.push(`### ${g.label}`, "", "| Platform | What it costs you | Best for | AI rules and notes |", "|---|---|---|---|");
  g.rows.forEach(r => L.push(`| [${cell(r.name)}](${r.url}) | ${cell(r.fee)} | ${cell(r.best)} | ${cell(r.ai)} |`));
  L.push("");
});
L.push("### Fee presets used by the page's calculator", "");
DATA.fees.forEach(f => L.push(`- **${f.name}:** ${f.note}`));
L.push("", "## Rules", "", md(copy.__RULES_SUB__), "", "### Do", "");
DATA.rulesDo.forEach(r => L.push(`- ${md(r)}`));
L.push("", "### Don't", "");
DATA.rulesDont.forEach(r => L.push(`- ${md(r)}`));
L.push("", ...copy.__RULES_CALLOUT__.match(/<p class="callout">.*?<\/p>/g).map(p => "> " + md(p).replace(/\\"/g, '"') + "\n"));
L.push("## 30-day plan", "", "Built for zero reviews. Tick items off as you go.", "");
DATA.plan.forEach(w => {
  L.push(`### ${w.title} (${w.days})`, "", `*Goal: ${w.goal}*`, "");
  w.items.forEach(t => L.push(`- [ ] ${t}`));
  L.push("");
});
L.push("## Templates", "", "Each template is also a separate file in [`templates/`](templates/).", "");
DATA.templates.forEach(t => L.push(`- [${t.title}](templates/${t.file}.md): ${t.use}`));
L.push("", "## Using this workspace", "");
DATA.workspace.forEach(w => L.push(`- **${w.t}.** ${w.d}`));
L.push("", "## Sources", "", md(copy.__SRC_SUB__), "");
DATA.sources.forEach(g => {
  L.push(`### ${g.label}`, "");
  g.items.forEach(u => L.push(`- <${typeof u === "string" ? u : u[1]}>`));
  L.push("");
});
fs.writeFileSync(path.join(REPO, "PLAYBOOK.md"), L.join("\n"));

fs.mkdirSync(path.join(REPO, "templates"), {recursive: true});
for (const t of DATA.templates) {
  fs.writeFileSync(path.join(REPO, "templates", t.file + ".md"), `# ${t.title}\n\n*${t.use}*\n\n\`\`\`text\n${t.text}\n\`\`\`\n`);
}
console.log(JSON.stringify({opps: opps.length, platforms: nPlatforms, sources: nSources, artifactBytes: artifact.length}));
