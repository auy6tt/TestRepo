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
for (const f of ["opportunities-services.js", "opportunities-ai-products.js", "results-picks-platforms-rules.js", "plan-and-templates.js", "first-clients.js", "niches.js", "sources.js"]) {
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
for (const n of get("NICHES")) {
  for (const k of ["id","group","rank","name","short","who","need","demand","why","price","how","where","first","risk","s"]) if (n[k] === undefined) throw new Error("niche " + n.id + " missing " + k);
  if (!get("NICHE_GROUPS")[n.group]) throw new Error("bad niche group " + n.group);
  if (n.s.length !== 4 || n.s.some(v => v < 1 || v > 5)) throw new Error("bad scores " + n.id);
}
{
  const nids = new Set(get("NICHES").map(n => n.id)), oids = new Set(opps.map(o => o.id));
  for (const n of get("NICHES")) for (const r of (n.related || [])) {
    const ok = r.startsWith("opp:") ? oids.has(r.slice(4)) : nids.has(r);
    if (!ok) throw new Error("niche " + n.id + " has unknown related " + r);
  }
}
const ranks = opps.map(o => o.rank);
if (new Set(ranks).size !== ranks.length) throw new Error("duplicate ranks");

const DATA = {
  cats: CATS, opps, picks: get("PICKS"), fees: get("FEES"), platformGroups: get("PLATFORM_GROUPS"),
  rulesDo: get("RULES_DO"), rulesDont: get("RULES_DONT"), plan: get("PLAN"), templates: get("TEMPLATES"),
  workspace: get("WORKSPACE"), sources: get("SOURCES"),
  niches: get("NICHES"), nicheGroups: get("NICHE_GROUPS"), glossary: get("GLOSSARY").slice().sort((a, b) => a[0].toLowerCase().localeCompare(b[0].toLowerCase())), whenWrong: get("WHEN_WRONG"),
  channels: get("CHANNELS"), upworkSteps: get("UPWORK_STEPS"), fiverrSteps: get("FIVERR_STEPS"), proofSteps: get("PROOF_STEPS")
};
const STAGES = get("STAGES"), PRINCIPLES = get("PRINCIPLES");
const nSources = DATA.sources.reduce((n, g) => n + g.items.length, 0);
const nPlatforms = DATA.platformGroups.reduce((n, g) => n + g.rows.length, 0);

const esc = s => String(s).replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;").replace(/"/g, "&quot;");

const copy = {
  __DATE__: "October 2026",
  __NSRC__: String(nSources),
  __LEDE__: "What people pay for that Claude can do well, where to find buyers when nobody knows you yet, and a 30-day plan to your first paid job. <strong>Ranked for someone starting from zero:</strong> no reviews, no portfolio, no network.",
  __META__: `<span><b>${opps.length}</b> ways to earn</span><span><b>${get("NICHES").length}</b> hidden niches</span><span><b>${nPlatforms}</b> platform entries</span><span><b>${get("NICHES").filter(n => n.kit).length}</b> starter kits</span><span>Prices in USD</span>`,
  __PICKS_SUB__: "Each pick either lets the buyer see the work before paying, or is small enough that buyers will take a chance on a newcomer. Start the first one this week and add others as reviews come in. The next section lists less crowded niches, several with a ready-made starter kit.",
  __NICHES_SUB__: "Each one passed three tests: proof that people pay for it, evidence that few people offer it, and work Claude can do most of. Many exist because a new rule, a platform change or a dull task created demand faster than sellers appeared. Scores are out of 5. Before you build anything, run the one-day test in each entry.",
  __FC_SUB__: "Marketplaces now rank sellers by their history, and AI matchers on both Upwork and Fiverr decide who gets seen. So a newcomer wins fastest through people they know and through outreach that shows finished work first. Run Upwork and Fiverr alongside as slower channels. Ranked by how fast each works for someone with zero reviews.",
  __REALITY_SUB__: "Claude makes the work fast. It doesn't bring clients and it doesn't make strangers trust you. The data is sobering. One tracker of Claude Code businesses listed by their owners found fewer than half earned anything, and the median listing made roughly $150–230 a month (self-reported). The ranges below are targets for someone who works the plan every week, not promises.",
  __STAGES__: STAGES.map(s => `<div class="stage"><div class="when">${esc(s.when)}</div><div class="amt">${esc(s.amt)}</div><p>${esc(s.text)}</p></div>`).join(""),
  __PRINCIPLES__: PRINCIPLES.map(p => `<li><b>${esc(p[0])}</b>${esc(p[1])}</li>`).join(""),
  __EXPLORE_SUB__: "Every option the research turned up, with prices, where buyers are, and how Claude does the work in this workspace. Open a row for details. \"First $\" is the typical time until your first payment arrives. \"No reviews needed\" means buyers judge the work or product itself; \"With samples\" means a newcomer can win with a portfolio and a low first price.",
  __WHERE_SUB__: "What each platform costs you and its rules on AI. Fees change, so check the platform before you rely on a number. The calculator shows what you keep after fees and your Claude plan.",
  __RULES_SUB__: "Anthropic's consumer terms allow you to sell work made with Claude. Most of the ways people get banned or burned come from the rules below. Anthropic's terms were read directly; platform rules mostly come from search summaries, so confirm them on each platform.",
  __RULES_CALLOUT__: `<p class="callout"><b>Scam rule:</b> if someone wants money from you before you've earned anything, or wants to move you to Telegram or WhatsApp right away, walk away. The FTC reports record losses to \"pay to get paid\" job scams.</p><p class="callout"><b>Side income that needs no reviews, but no Claude either:</b> AI-training platforms (Outlier, Mercor, Alignerr) pay roughly $15–$60+ an hour if you pass their tests, and research sites pay for your opinions (Prolific pays at least $8 an hour; UserTesting pays $10 per short test). All of them ban AI tools or detect them, and using Claude there also breaks Anthropic's usage policy, so this work must be done by you personally. Several are limited to certain countries: DataAnnotation, for example, only accepts six English-speaking countries.</p>`,
  __PLAN_SUB__: "Built for zero reviews and about 10–15 hours a week. Your progress is saved in this browser only.",
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
const SPEED = {1:"Days", 2:"Weeks", 3:"Months"};
const ZERO = {2:"Yes", 1:"With samples", 0:"Needs a track record"};
const L = [];
L.push("# Claude Income Playbook", "");
L.push("What people pay for that Claude can do well, where to find buyers when nobody knows you yet, and a 30-day plan to your first paid job. Ranked for someone starting from zero: no reviews, no portfolio, no network.", "");
if (PAGE_URL) L.push(`**Interactive version (filters, fee calculator, checklist):** ${PAGE_URL}`, "");
L.push(`Researched October 2026 · ${opps.length} ways to earn · ${get("NICHES").length} hidden niches · ${nPlatforms} platform entries · ${nSources} sources. Not legal, tax or financial advice.`, "");
L.push("## Contents", "", "1. [Start here](#start-here)", "2. [Hidden niches: real demand, few competitors](#hidden-niches-real-demand-few-competitors)", "3. [First clients when nobody knows you](#first-clients-when-nobody-knows-you)", "4. [Reality check](#reality-check)", "5. [All opportunities](#all-opportunities)", "6. [Where to sell](#where-to-sell)", "7. [Rules](#rules)", "8. [30-day plan](#30-day-plan)", "9. [Templates](#templates)", "10. [Using this workspace](#using-this-workspace)", "11. [Glossary](#glossary)", "12. [Sources](#sources)", "");
L.push("## Start here", "", md(copy.__PICKS_SUB__), "");
L.push("| # | Pick | Charge | First $ | Sell on |", "|---|---|---|---|---|");
DATA.picks.forEach((p, i) => L.push(`| ${i + 1} | **${cell(p.name)}**: ${cell(p.what)} ${cell(p.why)} | ${cell(p.price)} | ${cell(p.first)} | ${cell(p.where)} |`));
const NG = get("NICHE_GROUPS"), NN = get("NICHES").slice().sort((a, b) => a.rank - b.rank);
const ntotal = n => n.s.reduce((x, y) => x + y, 0);
L.push("", "## Hidden niches: real demand, few competitors", "", md(copy.__NICHES_SUB__), "");
L.push("| Niche | Type | Typical price | Demand | Few competitors | Claude fit | Beginner |", "|---|---|---|---|---|---|---|");
NN.slice().sort((a, b) => ntotal(b) - ntotal(a) || a.rank - b.rank).forEach(n => L.push(`| [${cell(n.name)}](#${n.id}) | ${NG[n.group]} | ${cell(n.price)} | ${n.s[0]} | ${n.s[1]} | ${n.s[2]} | ${n.s[3]} |`));
L.push("");
for (const g of Object.keys(NG)) {
  const list = NN.filter(n => n.group === g);
  if (!list.length) continue;
  L.push(`### ${NG[g]}`, "");
  list.forEach(n => {
    L.push(`<a id="${n.id}"></a>`, `#### ${n.name}`, "", `*${n.short}.* **${n.price}** · demand ${n.s[0]}/5 · few competitors ${n.s[1]}/5 · Claude fit ${n.s[2]}/5 · beginner ${n.s[3]}/5`, "");
    L.push(`- **Who pays:** ${md(n.who)}`, `- **What they need:** ${md(n.need)}`, `- **Proof of demand:** ${md(n.demand)}`, `- **Why few people offer it:** ${md(n.why)}`, `- **How Claude does it here:** ${md(n.how)}`, `- **Where buyers are:** ${md(n.where)}`, `- **Watch out:** ${md(n.risk)}`, `- **Test it in one day:** ${md(n.first)}`);
    if (n.related) L.push(`- **Related:** ` + n.related.map(r => { const isOpp = r.startsWith("opp:"); const id = isOpp ? r.slice(4) : r; const t = (isOpp ? opps : NN).find(x => x.id === id); return t ? `[${t.name}](#${id})` : null; }).filter(Boolean).join(", "));
    if (n.kit) L.push(`- **Starter kit:** [\`kits/${n.kit}/\`](kits/${n.kit}/). In Claude Code, type \`/${n.kit}\` in this repo.`);
    L.push("");
  });
}
L.push("", "## First clients when nobody knows you", "", md(copy.__FC_SUB__), "");
DATA.channels.forEach((c, i) => L.push(`${i + 1}. **${c.name}** (cost: ${c.cost}; first $: ${c.first}). ${c.what} ${c.why}`));
L.push("", "### Upwork, step by step", "");
DATA.upworkSteps.forEach((t, i) => L.push(`${i + 1}. ${t}`));
L.push("", "### Fiverr, step by step", "");
DATA.fiverrSteps.forEach((t, i) => L.push(`${i + 1}. ${t}`));
L.push("", "### Show-first outreach, step by step", "");
DATA.proofSteps.forEach((t, i) => L.push(`${i + 1}. ${t}`));
L.push("", "## Reality check", "", md(copy.__REALITY_SUB__), "");
STAGES.forEach(s => L.push(`- **${s.when}: ${s.amt}.** ${s.text}`));
L.push("");
PRINCIPLES.forEach(p => L.push(`- **${p[0]}** ${p[1]}`));
L.push("", "## All opportunities", "", md(copy.__EXPLORE_SUB__), "");
L.push("*First $ is the typical time until your first payment arrives. Claude fit: ●●● means Claude can do most of the work.*", "");
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
L.push("### Fee presets used by the interactive page's calculator", "");
DATA.fees.forEach(f => L.push(`- **${f.name}:** ${f.note}`));
L.push("", "## Rules", "", md(copy.__RULES_SUB__), "", "### Do", "");
DATA.rulesDo.forEach(r => L.push(`- ${md(r)}`));
L.push("", "### Don't", "");
DATA.rulesDont.forEach(r => L.push(`- ${md(r)}`));
L.push("", "### When a job goes wrong", "");
DATA.whenWrong.forEach(r => L.push(`- ${md(r)}`));
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
L.push("", "## Glossary", "");
DATA.glossary.forEach(g => L.push(`- **${g[0]}:** ${g[1]}`));
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
