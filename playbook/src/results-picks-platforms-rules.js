var OPPS_RESULTS = [
{id:"hackathons", cat:"results", rank:29, zero:2, speed:2, fit:3, value:500,
 name:"Online AI hackathons",
 short:"Judged on a working demo, not on your reviews",
 price:"$500–$5,000 prizes (credits are more common)",
 need:"AI companies sponsor hackathons to get developers building on their tools. Judges score the demo, not who you are.",
 how:"Claude Code builds fast. Ship a live demo page and a 2–3 minute video, and keep a starter kit you reuse between events.",
 where:"devpost.com (filter for online events), lablab.ai sponsor tracks (Sept–Oct 2026 pools of $6,000–12,000), Claude-linked events (often selective, often paid in credits).",
 signal:"Devpost AI hackathons ran $80k–$2M prize pools in 2025–2026. Side-track prizes (\"best use of X\") are where small teams win.",
 risk:"Hundreds to thousands of entries, so roughly a 1–5% chance of placing per entry (estimate). lablab.ai payouts can take up to 90 days. Check country eligibility before building.",
 skill:"Low to medium. The pitch video matters a lot.",
 gig:"Target: a sponsor side-track at an online lablab.ai or Devpost event"},
{id:"expensify", cat:"results", rank:32, zero:2, speed:2, fit:2, value:250,
 name:"Expensify's paid GitHub issues",
 short:"A company that pays outsiders a fixed fee per accepted fix",
 price:"$250 per fix",
 need:"Expensify pays outside developers to fix issues labeled \"Help Wanted\" in its open-source app.",
 how:"Post a proposal on the issue. If you're selected, Claude Code helps you write and test the fix. You're paid through Upwork at least 7 days after the fix reaches production.",
 where:"github.com/Expensify/App, issues labeled Help Wanted. Read CONTRIBUTING.md and AI_ETIQUETTE.md first.",
 signal:"$250 is standard, with occasional larger jobs (one $3,000 integration in Aug 2026). The most reliable payer in this category.",
 risk:"Busy: new $250 issues drew 23–55 comments. You lose 50% for each bug your fix causes. AI use is allowed, but you must understand and test the code. Needs a verified Upwork account.",
 skill:"Medium. Expect a few weeks learning a large React Native codebase.",
 gig:"Target: one accepted proposal in your first month"},
{id:"oss-bounties", cat:"results", rank:33, zero:2, speed:2, fit:2, value:100,
 name:"Open-source bounties",
 short:"Cash on GitHub issues through Algora or Opire",
 price:"$50–$500, most under $150",
 need:"Companies put cash on GitHub issues. The person whose fix is merged is paid and keeps 100%.",
 how:"Claude Code reproduces the bug, writes the fix and the tests.",
 where:"algora.io/bounties and opire.dev. Niche languages (Rust, Elixir, Scala, C++ or GPU code) are far less crowded than TypeScript and React.",
 signal:"On 30 Sept 2026 there were 155 open bounties worth $68.8k, and 124 of them paid under $150.",
 risk:"Flooded by AI agents: one $170 bounty drew 158 attempts, and generic bounties work out to about $1–5 an hour. Many repos ban or auto-close AI pull requests. Payouts need Stripe Connect in your country. Skip any bounty with 3+ claimants or a linked PR.",
 skill:"Medium.",
 gig:"Rule: skip any bounty with 3+ claimants or a linked pull request"},
{id:"kaggle", cat:"results", rank:34, zero:2, speed:3, fit:2, value:0,
 name:"Kaggle and data competitions",
 short:"Good for your profile, rarely for cash",
 price:"Usually $0 cash",
 need:"Companies post prediction problems, and the top few teams win prizes.",
 how:"Claude helps you build strong starting models in notebooks quickly.",
 where:"kaggle.com, zindi.africa, drivendata.org.",
 signal:"The best AI agents now win a medal in 61–64% of past Kaggle competitions (MLE-bench, 2026). Medals are easy; prize places are not.",
 risk:"Prizes go to the top 3–5 of thousands of teams. Code competitions run offline, so you can't call Claude at submission time.",
 skill:"Medium to high.",
 gig:"Use for a portfolio line such as a Kaggle medal, not for income"},
{id:"bug-bounties", cat:"results", rank:35, zero:2, speed:3, fit:1, value:0,
 name:"Security bug bounties",
 short:"Paid per valid, reproducible vulnerability",
 price:"Most beginners earn $0",
 need:"Companies pay for security vulnerabilities that are real, in scope and reproducible.",
 how:"Claude helps you read code and explore. You must confirm every finding yourself and write the report.",
 where:"hackerone.com, bugcrowd.com, intigriti.com, yeswehack.com.",
 signal:"Report volume more than doubled after Feb 2026 as AI tools flooded programs. curl ended paid bounties in Jan 2026, and Google's open-source program paused on 1 Oct 2026.",
 risk:"Unchecked AI reports get you suspended (Bugcrowd: 30 days) or banned (YesWeHack). Only test targets that are in scope.",
 skill:"High. Only worth it if you want to learn security seriously.",
 gig:"Only if you want to learn security seriously"}
];

var PICKS = [
 {name:"Spreadsheet and PDF-to-Excel fixes",
  what:"Fix formulas, clean data, turn PDFs into spreadsheets, build simple dashboards.",
  why:"Small, cheap jobs are the ones buyers will risk on a newcomer. Claude does them in minutes, and you can check every number before delivering.",
  price:"$20–$250 per job", first:"Days", where:"Fiverr, Upwork, r/forhire, people you know"},
 {name:"Show-first websites for local businesses",
  what:"Find businesses with no website, build theirs first, then offer to put it live with a monthly care plan.",
  why:"Reviews don't matter when the owner can see the finished site before paying anything. The care plan turns one sale into monthly income.",
  price:"$300–$800 + $50–150/mo", first:"1–3 weeks", where:"Google Maps prospecting, walking in, local groups"},
 {name:"Fixing apps people built with AI tools",
  what:"Diagnose and fix stuck Lovable, Bolt, Replit and Base44 projects, then help them launch.",
  why:"Demand is new and growing fast, so established sellers haven't taken it over, and Claude Code is very strong at it. Sell a fixed-price diagnosis first.",
  price:"$50–$500 per fix", first:"1–2 weeks", where:"Fiverr Vibe Coding category, Upwork, tool communities"},
 {name:"Small automations for businesses",
  what:"n8n, Make, Zapier and Apps Script flows that move data, answer leads and build reports.",
  why:"Start by fixing someone's existing workflow for a small fixed fee. Every build can carry a monthly care plan.",
  price:"$150–$500, then $1,500+", first:"2–4 weeks", where:"Upwork, Fiverr n8n category, LinkedIn"},
 {name:"Resumes and LinkedIn for one profession",
  what:"ATS-friendly resume and LinkedIn rewrite matched to real job ads.",
  why:"Everyone knows someone job hunting, so this is the quickest route to a first paid job and a first testimonial through people who already trust you.",
  price:"$50–$150 to start", first:"Days", where:"People you know first, then Fiverr"},
 {name:"Hackathons and one Apify tool on the side",
  what:"Enter online AI hackathons, and publish one niche data tool on the Apify Store.",
  why:"Judges and marketplace buyers look at the work, not your reviews, and both leave you with public portfolio pieces. Treat the money as a bonus.",
  price:"Prizes $500–$5,000; Apify $0–300/mo", first:"Weeks to months", where:"devpost.com, lablab.ai, apify.com"}
];

var STAGES = [
 {when:"First 30 days", amt:"$0–$200", text:"Most of the month goes into samples, profiles and outreach. One or two small paid jobs and a first review count as a good result."},
 {when:"Months 2–3", amt:"$200–$1,000/mo", text:"Reviews and referrals start to stack up if you keep sending 10–20 messages or proposals every week."},
 {when:"Months 4–6", amt:"$1,000–$3,000/mo", text:"Reached by people who pick one niche, raise prices after each batch of reviews and sell monthly care plans. Many never get here."}
];

var PRINCIPLES = [
 ["Sell finished results, not AI output.", "Buyers can run Claude themselves. Upwork's 2026 data: complex AI work earns 45% more per contract, while generic generated content earns 13% less."],
 ["Show the work before asking for trust.", "Samples, demos and before-and-after examples replace the reviews you don't have yet."],
 ["Say your niche out loud.", "\"Spreadsheets for property managers\" gets replies. \"AI services\" doesn't."],
 ["Spend most of your time finding clients.", "Building is nearly free now. The famous AI-built successes all started with an audience or a network."],
 ["Fixed scope, fixed price.", "Diagnose first, then quote. It protects you from endless revisions."],
 ["Turn every job into monthly income.", "Offer a care plan or retainer with every delivered project."],
 ["Check everything before it ships.", "Anthropic gives no accuracy guarantee on outputs, and your name is on the work."],
 ["Ignore \"make money with AI\" courses.", "The FTC shut down Click Profit in 2025 after it took at least $14M with fake AI income promises."]
];

var FEES = [
 {name:"Fiverr", pct:20, fixed:0, min:0, note:"Fiverr keeps 20% of every order. New sellers wait 14 days for money to clear."},
 {name:"Upwork (typical 10%)", pct:10, fixed:0, min:0, note:"Upwork's fee is 0–15% per contract and is shown before you apply; 10% is a typical value. Each proposal also costs Connects ($0.15 each, usually 2–16 per job)."},
 {name:"Upwork (15%, worst case)", pct:15, fixed:0, min:0, note:"Upwork's fee varies by contract, up to 15%. Proposals also cost Connects."},
 {name:"Contra", pct:0, fixed:0, min:0, note:"You keep 100%. The client pays a small fee per payment."},
 {name:"Freelancer.com", pct:10, fixed:0, min:5, note:"Freelancer.com takes 10% of fixed-price jobs, at least $5."},
 {name:"PeoplePerHour (first £500 per client)", pct:20, fixed:0, min:0, note:"20% until you've billed a client £500, then 7.5%, then 3.5% above £5,000."},
 {name:"Direct client, card payment (approx.)", pct:2.9, fixed:0.30, min:0, note:"A typical card processor fee (about 2.9% + $0.30 in the US). International cards and currency conversion cost more."},
 {name:"Etsy digital download (US, approx.)", pct:9.5, fixed:0.45, min:0, note:"$0.20 listing + 6.5% transaction + about 3% + $0.25 processing. Offsite Ads take another 12–15% on sales they bring."},
 {name:"Gumroad, direct sale", pct:10, fixed:0.50, min:0, note:"Gumroad takes 10% + $0.50 on your own traffic, 30% on sales from its Discover page. It handles sales tax for you."},
 {name:"Apify Store", pct:20, fixed:0, min:0, note:"Apify keeps 20%, and platform compute costs also come out of your share."}
];

var PLATFORM_GROUPS = [
 {label:"Freelance marketplaces: clients come looking", rows:[
  {name:"Fiverr", url:"https://www.fiverr.com", fee:"20% per order", best:"Fixed-price packages. Buyers search for you, and applying costs nothing.", ai:"AI allowed. Disclose it if a buyer asks, honor \"no AI\" requests, and refine the output."},
  {name:"Upwork", url:"https://www.upwork.com", fee:"0–15% + Connects", best:"The biggest pool of jobs, including hourly and long-term work.", ai:"AI allowed and best disclosed. Bots or extensions that send proposals get accounts suspended."},
  {name:"Contra", url:"https://contra.com", fee:"0% to you", best:"Portfolio-led work, and a way to bill clients you find elsewhere.", ai:"No specific rule found."},
  {name:"Freelancer.com", url:"https://www.freelancer.com", fee:"10% (min $5)", best:"Contests and small cheap jobs; free bids are limited.", ai:"No specific rule found."},
  {name:"PeoplePerHour", url:"https://www.peopleperhour.com", fee:"20% → 7.5% → 3.5%", best:"UK and European small businesses.", ai:"No specific rule found."},
  {name:"Legiit", url:"https://legiit.com", fee:"15%", best:"SEO and digital marketing gigs.", ai:"No specific rule found."},
  {name:"Malt", url:"https://www.malt.com", fee:"10%, later 5% (0% UK/NL)", best:"European corporate clients.", ai:"No specific rule found."},
  {name:"Workana", url:"https://www.workana.com", fee:"20% → 10% → 5%", best:"Spanish and Portuguese-speaking clients.", ai:"No specific rule found."},
  {name:"Toptal, Arc.dev, Braintrust, Lemon.io", url:"https://www.toptal.com", fee:"0% shown to you", best:"Senior work after heavy vetting (Toptal accepts under 3%). Come back once you have a track record.", ai:"Screening is live; AI only helps on test projects."}
 ]},
 {label:"Selling products: the platform brings buyers", rows:[
  {name:"Apify Store", url:"https://apify.com/partners/actor-developers", fee:"20% + compute", best:"Scrapers and data tools; pay-per-event since 1 Oct 2026.", ai:"AI-built code is fine."},
  {name:"Etsy", url:"https://www.etsy.com", fee:"$0.20 + 6.5% + processing", best:"Spreadsheet and planner templates with search traffic.", ai:"AI use must be disclosed in the listing; reselling bought templates is banned."},
  {name:"Gumroad", url:"https://gumroad.com", fee:"10% + $0.50 (30% via Discover)", best:"Templates, packs and tools for your own audience; handles sales tax.", ai:"No specific rule found."},
  {name:"Payhip / Polar / Lemon Squeezy", url:"https://payhip.com", fee:"About 5% + fees", best:"Cheaper checkout for your own products.", ai:"No specific rule found."},
  {name:"Chrome Web Store + ExtensionPay", url:"https://extensionpay.com", fee:"5% via ExtensionPay", best:"Paid browser extensions.", ai:"Store policy review applies."},
  {name:"Shopify App Store", url:"https://shopify.dev/docs/apps/launch/distribution/revenue-share", fee:"0% on first $1M, then 15%", best:"Monthly-subscription merchant tools.", ai:"App review applies."},
  {name:"Notion Marketplace", url:"https://www.notion.com/templates", fee:"10% + $0.40", best:"Niche business templates.", ai:"No specific rule found."},
  {name:"Agensi / MCPize", url:"https://www.agensi.io", fee:"You keep 70–85%", best:"Claude skills and MCP servers; small sums.", ai:"Security scan on listings."},
  {name:"Envato, Teachers Pay Teachers, Udemy, KDP", url:"https://www.teacherspayteachers.com", fee:"Up to 50–85% taken", best:"Mostly avoid: Envato takes 50% from Jul 2026; TpT pays 55% on its basic plan; Udemy's subscription share fell to 15%.", ai:"KDP and others require AI disclosure."}
 ]},
 {label:"Paid on results", rows:[
  {name:"Devpost", url:"https://devpost.com", fee:"Free to enter", best:"Online hackathons with cash and credit prizes.", ai:"Usually must use the sponsor's tools; check each ruleset."},
  {name:"lablab.ai", url:"https://lablab.ai/ai-hackathons", fee:"Free to enter", best:"Frequent AI hackathons with $6k–12k pools.", ai:"Must use the sponsor's tech; payouts up to 90 days."},
  {name:"Expensify/App", url:"https://github.com/Expensify/App", fee:"Upwork fee applies", best:"$250 fixed bounties for accepted fixes.", ai:"Allowed if you understand and test the code; 50% penalty per regression."},
  {name:"Algora / Opire", url:"https://algora.io/bounties", fee:"You keep 100%", best:"Cash on GitHub issues; very crowded.", ai:"Set per repo; many ban AI pull requests."},
  {name:"Kaggle", url:"https://www.kaggle.com", fee:"Free", best:"Medals for your profile.", ai:"Code competitions run offline."}
 ]},
 {label:"Getting paid (availability depends on your country)", rows:[
  {name:"Payoneer", url:"https://www.payoneer.com", fee:"Varies", best:"Receiving marketplace payouts in many countries.", ai:"Check that it supports your country and bank."},
  {name:"Wise", url:"https://wise.com", fee:"Low conversion fees", best:"Holding and converting foreign currency.", ai:"Check that it supports your country and bank."},
  {name:"PayPal", url:"https://www.paypal.com/webapps/mpp/country-worldwide", fee:"About 3–5% + fixed fee", best:"Direct clients, Apify payouts from $20.", ai:"Some countries can send but not receive."},
  {name:"Stripe", url:"https://stripe.com/global", fee:"About 2.9% + $0.30 (US)", best:"Card payments; Algora and Opire bounty payouts.", ai:"Only in Stripe-supported countries."}
 ]}
];

var RULES_DO = [
 "<b>Sell work made with Claude.</b> Anthropic's consumer terms assign outputs to you (\"if any\") and don't forbid commercial use. They also give no accuracy guarantee, so check everything.",
 "<b>Turn off model training before client work</b> at claude.ai/settings/data-privacy-controls. With it on, chats are kept 5 years; off, 30 days. Don't rate client chats with thumbs, which saves them, and delete finished client sessions.",
 "<b>Run anything a client uses on an API key.</b> That means chatbots, agents and automations, on the client's own key or yours billed to them. List API usage as a separate cost line.",
 "<b>Tell clients you use AI tools</b> and honor any \"no AI\" request. Fiverr requires disclosure when asked.",
 "<b>Protect your payment.</b> Take 30–50% upfront or use platform escrow. Hand over rights only after full payment, and cap your liability at the fee.",
 "<b>Keep the client's things in the client's name:</b> domains, hosting, API keys, accounts.",
 "<b>Plan around usage limits.</b> Max resets every 5 hours and also has a weekly cap shared by Claude and Claude Code. If ANTHROPIC_API_KEY is set, Claude Code bills that key instead.",
 "<b>Check your local rules</b> for freelance permits and tax registration before you send invoices."
];
var RULES_DONT = [
 "<b>Don't share or rent your Claude account,</b> or let a client use your login. Offers to \"be the face\" of an account are linked to fraud rings.",
 "<b>Don't run client bots or apps on your Max login</b> or resell \"Claude access\". Anthropic forbids routing other people's usage through Pro or Max plans.",
 "<b>Don't write students' graded work,</b> fake reviews, spam or mass-produced SEO pages. All of these break Anthropic's usage policy, and some are crimes.",
 "<b>Don't use Claude on AI-training platforms</b> such as Outlier, DataAnnotation and Mercor. They ban it and keep your pay.",
 "<b>Don't move Upwork or Fiverr clients off-platform.</b> Both ban it.",
 "<b>Don't use bots to send proposals</b> or to create accounts.",
 "<b>Don't pay to get a job,</b> cash an \"overpayment\" check, or move to Telegram or WhatsApp because a stranger insists.",
 "<b>Don't run a stranger's \"test project\" repo without reading it first.</b> Fake coding tests have carried malware.",
 "<b>Don't promise \"compliant\", \"secure\" or \"guaranteed rankings\".</b> Describe what you checked, and when.",
 "<b>Don't paste client passwords or personal data</b> into chats unless your agreement allows AI tools."
];

var WORKSPACE = [
 {t:"One folder or repo per job", d:"Ask Claude to set up a folder or repo for each client and to commit and push as it goes. This cloud container is temporary and is deleted after a period of inactivity."},
 {t:"Real office files", d:"Ask for .xlsx, .docx, .pptx or .pdf. Claude has skills for each, so spreadsheets keep working formulas and documents keep real formatting."},
 {t:"A browser for checking", d:"Headless Chromium and Playwright are installed. Use them for phone and desktop screenshots, form testing, and speed or accessibility audits."},
 {t:"Private pages like this one", d:"Claude can publish private pages for your portfolio, price sheet or reports. Client-branded sites go on hosting in the client's name, not here."},
 {t:"Network access", d:"This environment's network policy blocked many sites during research (Upwork, Etsy, Wikipedia, the FTC). For scraping or auditing client sites, change Network access in the environment settings."},
 {t:"Secrets stay secret", d:"Don't paste client passwords into chat. Use temporary accounts and the environment's secrets settings, and never commit keys to Git."}
];
