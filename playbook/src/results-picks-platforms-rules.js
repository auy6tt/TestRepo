var OPPS_RESULTS = [
{id:"hackathons", cat:"results", rank:29, zero:2, speed:3, fit:3, value:500,
 name:"Online AI hackathons",
 short:"Judged on a working demo, not on your reviews",
 price:"$500–$5,000 prizes (credits are more common)",
 need:"AI companies sponsor hackathons to get developers building on their tools. Judges score the demo, not who you are.",
 how:"Claude Code builds fast. Ship a live demo page and a 2–3 minute video, and keep a starter kit you reuse between events.",
 where:"devpost.com (filter for online events), lablab.ai sponsor tracks (Sept–Oct 2026 pools of $6,000–12,000), Claude-linked events (often selective, often paid in credits).",
 signal:"Big events are crowded (one Kaggle-hosted hackathon drew about 1,600 submissions for roughly 14 prizes), but smaller ones aren't: DeveloperWeek NY 2026 had 612 participants for $9,250 in cash. Only 5–33% of people who register on Devpost ever submit, so finishing alone puts you ahead.",
 risk:"Pick smaller online events (a few hundred participants) with a sponsor side-track. Many prizes are paid in API credits, and lablab.ai payouts can take up to 90 days. Check the rules on AI disclosure, building during the event, and country eligibility.",
 skill:"Low to medium. The pitch video matters a lot.",
 gig:"Target: a sponsor side-track at an online lablab.ai or Devpost event"},
{id:"expensify", cat:"results", rank:32, zero:2, speed:3, fit:2, value:250,
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
 risk:"Flooded by AI agents: one $170 bounty drew 158 attempts, and generic bounties work out to about $1–5 an hour. Many repos ban or auto-close AI pull requests. Payouts go through Stripe, and in some countries (for example the UAE and India) only registered businesses can receive them.",
 skill:"Medium.",
 gig:"Rule: skip any bounty with 3+ claimants or a linked pull request"},
{id:"contests", cat:"results", rank:36, zero:2, speed:1, fit:2, value:40,
 name:"Small contests on Freelancer.com",
 short:"Naming, writing and Excel or data-entry contests",
 price:"$20–$190 prizes",
 need:"Buyers post a contest and pay the best entry. A win also gives you a first review on the platform.",
 how:"Claude helps you produce strong entries quickly. Read each contest brief closely and tailor your entry to it.",
 where:"freelancer.com/contest. Filter for guaranteed contests with 50 or fewer entries.",
 signal:"Sampled naming contests paid $20–50 and drew 45–277 entries. A data-entry contest drew 129.",
 risk:"Low odds per entry, so treat it as practice and a source of a first review. Freelancer.com takes 10% of the prize or $5, whichever is more. Atom (formerly Squadhelp), a separate naming-contest site, bans name generators, AI included.",
 skill:"Low.",
 gig:"Target: 3–5 strong entries a week for a month, then check your win rate"},
{id:"kaggle", cat:"results", rank:34, zero:2, speed:3, fit:2, value:0,
 name:"Kaggle and data competitions",
 short:"Good for your profile, rarely for cash",
 price:"Usually $0 cash",
 need:"Companies post prediction problems, and the top few teams win prizes.",
 how:"Claude helps you build strong starting models in notebooks quickly.",
 where:"kaggle.com, zindi.africa, drivendata.org.",
 signal:"The best AI agents now win a medal in 61–64% of past Kaggle competitions (MLE-bench, 2026). With AI help, medals are achievable; prize money rarely is.",
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
  why:"Small, cheap jobs are the ones buyers will risk on a newcomer, and Fiverr searches for Excel data cleaning rose 210% in six months. Claude does the work in minutes, and you can check every number before delivering.",
  price:"$20–$250 per job", first:"Days", where:"People you know, r/forhire, Upwork, Fiverr"},
 {name:"Show-first websites for local businesses",
  what:"Find businesses with no website, build theirs first, then offer to put it live with a monthly care plan.",
  why:"Reviews don't matter when the owner can see the finished site before paying anything. The care plan turns one sale into monthly income.",
  price:"$300–$800 + $50–150/mo", first:"2–6 weeks", where:"Google Maps prospecting, walking in, local groups"},
 {name:"Fixing apps people built with AI tools",
  what:"Diagnose and fix stuck Lovable, Bolt, Replit and Base44 projects, then help them launch.",
  why:"Demand is new and growing fast, so established sellers haven't taken it over, and Claude Code is very strong at it. Sell a fixed-price diagnosis first.",
  price:"$50–$500 per fix", first:"1–3 weeks", where:"Fiverr Vibe Coding category, Upwork, tool communities"},
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
 {when:"Months 4–6", amt:"$1,000–$3,000/mo", text:"A stretch target (our estimate) for people who pick one niche, raise prices after each batch of reviews and sell monthly care plans. Many never get here."}
];

var PRINCIPLES = [
 ["Sell finished results, not AI output.", "Buyers can run Claude themselves. Upwork's 2026 data: complex AI work earns 45% more per contract, while generic generated content earns 13% less."],
 ["Show the work before asking for trust.", "Samples, demos and before-and-after examples replace the reviews you don't have yet."],
 ["Say your niche out loud.", "\"Spreadsheets for property managers\" gets replies. \"AI services\" doesn't."],
 ["Spend most of your time finding clients.", "Building is nearly free now. Most of the famous AI-built successes started with an audience or a network."],
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
  {name:"Fiverr", url:"https://www.fiverr.com", fee:"20% per order", best:"Fixed-price packages. Buyers search for you, and applying costs nothing. Its AI matcher (Mira) favors sellers who already have orders.", ai:"AI allowed. Disclose it if a buyer asks, honor \"no AI\" requests, and refine the output. Friends ordering to create reviews means a permanent ban."},
  {name:"Upwork", url:"https://www.upwork.com", fee:"0–15% + Connects", best:"The biggest pool of jobs. One profile per person since May 2026, and its AI (Uma) shortlists freelancers for clients.", ai:"AI allowed and best disclosed. Bots or extensions that send proposals get accounts suspended."},
  {name:"Contra", url:"https://contra.com", fee:"0% to you", best:"Portfolio-led work, and a way to bill clients you find elsewhere.", ai:"No specific rule found."},
  {name:"Freelancer.com", url:"https://www.freelancer.com", fee:"10% or $5, whichever is more", best:"Contests and small cheap jobs; free bids are limited.", ai:"No specific rule found."},
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
  {name:"Envato, Teachers Pay Teachers, Udemy, KDP", url:"https://www.teacherspayteachers.com", fee:"Large cuts", best:"Mostly avoid: Envato takes 50% from July 2026, Teachers Pay Teachers keeps 45% on its basic plan, and Udemy pays instructors 15% of subscription revenue.", ai:"KDP and others require AI disclosure."}
 ]},
 {label:"Paid on results", rows:[
  {name:"Devpost", url:"https://devpost.com", fee:"Free to enter", best:"Online hackathons with cash and credit prizes.", ai:"Usually must use the sponsor's tools; check each ruleset."},
  {name:"lablab.ai", url:"https://lablab.ai/ai-hackathons", fee:"Free to enter", best:"Frequent AI hackathons with $6,000–12,000 prize pools.", ai:"Must use the sponsor's tech; payouts up to 90 days."},
  {name:"Expensify/App", url:"https://github.com/Expensify/App", fee:"Upwork fee applies", best:"$250 fixed bounties for accepted fixes.", ai:"Allowed if you understand and test the code; 50% penalty per regression."},
  {name:"Algora / Opire", url:"https://algora.io/bounties", fee:"You keep 100%", best:"Cash on GitHub issues; very crowded.", ai:"Set per repo; many ban AI pull requests."},
  {name:"Kaggle", url:"https://www.kaggle.com", fee:"Free", best:"Medals for your profile.", ai:"Code competitions run offline."}
 ]},
 {label:"Getting paid (availability depends on your country)", rows:[
  {name:"Payoneer", url:"https://www.payoneer.com", fee:"Varies", best:"Marketplace payouts; Etsy pays sellers in some countries through it.", ai:"Check that it supports your country and bank."},
  {name:"Wise", url:"https://wise.com", fee:"Low conversion fees", best:"Holding and converting foreign currency.", ai:"Check that it supports your country and bank."},
  {name:"PayPal", url:"https://www.paypal.com/webapps/mpp/country-worldwide", fee:"About 3–5% + fixed fee", best:"Direct clients; Apify payouts from $20; UserTesting and Gumroad payouts.", ai:"Some countries can send but not receive."},
  {name:"Stripe", url:"https://stripe.com/global", fee:"About 2.9% + $0.30 (US)", best:"Card payments; Algora, Opire and Notion Marketplace payouts.", ai:"In some countries (for example the UAE and India) individuals need a business license, which blocks these payouts."}
 ]}
];

var RULES_DO = [
 "<b>Sell work made with Claude.</b> Anthropic's consumer terms assign outputs to you (\"if any\") and don't forbid commercial use. They also give no accuracy guarantee, so check everything.",
 "<b>Turn off model training before client work</b> at claude.ai/settings/data-privacy-controls. With it off, Anthropic's retention period is 30 days; with it on, data from new chats can be kept up to 5 years. Chats you don't delete stay in your history, and deleted ones are erased from Anthropic's systems within 30 days. Don't rate client chats with thumbs, which saves them.",
 "<b>Run anything a client uses on an API key.</b> That means chatbots, agents and automations, on the client's own key or yours billed to them. List API usage as a separate cost line and set a spending limit.",
 "<b>Tell clients you use AI tools</b> and honor any \"no AI\" request. Fiverr requires disclosure when asked, and any chatbot you build for a client must tell its users they're talking to an AI (Anthropic's usage policy).",
 "<b>Protect your payment.</b> Take 50% upfront (never less than 30%) or use platform escrow. Hand over rights only after full payment, and cap your liability at the fee.",
 "<b>Keep the client's things in the client's name:</b> domains, hosting accounts, API keys and other accounts.",
 "<b>Label samples as samples,</b> and say how you know anyone who gives you a testimonial.",
 "<b>Follow marketing rules when you contact strangers.</b> Send messages by hand, include an easy opt-out (\"Reply 'no' and I won't contact you again\"), put your postal address in US marketing emails (CAN-SPAM), get consent before emailing sole traders in the UK (PECR), and stop at the first no. Messaging apps ban numbers that get reported for spam.",
 "<b>Plan around usage limits.</b> Max resets every 5 hours and also has a weekly cap shared by Claude and Claude Code; you can buy extra usage if you hit it before a deadline. If ANTHROPIC_API_KEY is set, Claude Code bills that key instead.",
 "<b>Sort out tax and payout paperwork.</b> Check your local rules for freelance permits and tax registration before you invoice. Non-US sellers usually fill in form W-8BEN when a US platform asks. Keep a record of every payment. If you sell digital products directly, a merchant-of-record checkout (Gumroad, Lemon Squeezy, Paddle) handles sales tax and VAT for you."
];
var RULES_DONT = [
 "<b>Don't share or rent your Claude account,</b> or let a client use your login. Separately, offers to rent your freelancer account or identity, or to \"be the face\" of someone else's account, are linked to fraud rings.",
 "<b>Don't run client bots or apps on your Max login</b> or resell \"Claude access\". Anthropic forbids routing other people's usage through Pro or Max plans.",
 "<b>Don't write students' graded work,</b> fake reviews, spam or mass-produced SEO pages. All of these break Anthropic's usage policy, and some are crimes.",
 "<b>Don't use Claude on AI-training platforms</b> such as Outlier, DataAnnotation and Mercor. They ban it and keep your pay.",
 "<b>Don't move Upwork or Fiverr clients off-platform.</b> Both ban it.",
 "<b>Never offer anything in return for a review,</b> positive or not, and never have friends or family order your gigs to create reviews. Fiverr bans this permanently, and the US FTC can seek up to $53,088 per fake review (2025 figure). Bill people you know directly and ask them for a testimonial instead.",
 "<b>Don't use bots to send proposals</b> or to create accounts.",
 "<b>Don't pay to get a job,</b> cash an \"overpayment\" check, or move to Telegram or WhatsApp because a stranger insists.",
 "<b>Never run a stranger's \"test project\" on your own computer.</b> Fake coding tests hide malware in dependencies and install scripts that reading the code won't reveal. If you must run one, use a throwaway cloud environment with no saved logins, keys or wallets.",
 "<b>Don't promise \"compliant\", \"secure\" or \"guaranteed rankings\".</b> Describe what you checked, and when.",
 "<b>Never paste client passwords into chats,</b> and share client personal data with AI tools only if your agreement allows it."
];

var WHEN_WRONG = [
 "<b>The client wants more than you agreed.</b> Say yes with a price: \"Happy to add that; it's an extra $X and one more day.\" Write it down before you start.",
 "<b>The client pays late.</b> Send a polite reminder on the due date and a firmer one 7 days later, and pause further work until it's paid. On off-platform jobs, don't hand over final files before payment.",
 "<b>The client is unhappy.</b> Ask exactly what's wrong, fix anything within the agreed scope quickly, and offer a partial refund before it turns into a dispute.",
 "<b>A platform dispute starts.</b> Keep every message and delivery on the platform and use its resolution center. Cancellations hurt your Fiverr stats, so agree changes before an order starts.",
 "<b>You made a mistake.</b> Own it, fix it quickly at no charge, and tell the client what you changed so it doesn't happen again."
];

var WORKSPACE = [
 {t:"One folder or repo per client", d:"Ask Claude to set up a folder or repo for each client and to commit and push as it goes. This cloud container is temporary and is deleted after a period of inactivity."},
 {t:"A CLAUDE.md for each client", d:"Put the client's rules, style, file locations and quirks in a CLAUDE.md inside their project. Claude reads it at the start of every session, so you never re-explain."},
 {t:"Turn repeat work into a skill", d:"When you deliver the same thing twice, ask Claude to save the steps as a custom skill (a SKILL.md file in .claude/skills/your-skill-name/). The third delivery takes one command and comes out consistent."},
 {t:"Starter kits", d:"The kits folder has 10 starter kits covering 14 of the hidden niches, each with scripts, templates and a sample deliverable. Run bash kits/setup.sh at the start of each cloud session. Each kit comes with a skill: type its name after a slash (for example /board-minutes)."},
 {t:"Weekly deliverables on a schedule", d:"Routines (claude.ai/code/routines) run a saved task in the cloud on a schedule, even with your laptop closed: a weekly digest, a monthly report. You review the output and send it to your client yourself."},
 {t:"Real office files", d:"Ask for .xlsx, .docx, .pptx or .pdf. Claude has skills for each, so spreadsheets keep working formulas and documents keep real formatting."},
 {t:"A browser for checking", d:"Headless Chromium and Playwright are installed. Use them for phone and desktop screenshots, form testing, and speed or accessibility audits."},
 {t:"Private pages like this one", d:"Claude can publish private pages for your portfolio, price sheet or reports, and you can share one from the page's Share menu. For a public portfolio site, GitHub Pages or Cloudflare Pages work. Client-branded sites go on hosting in the client's name, not here."},
 {t:"Quote a fixed price", d:"Estimate your hours, multiply by your target hourly rate, add 30% for surprises, and quote that as a fixed price with a clear scope. Track your real hours on the first few jobs so later quotes get more accurate."},
 {t:"Stretch your usage limits", d:"Long chats and big files use up limits fastest. Start a fresh session per task, use /compact in long ones, pick a lighter model for routine work, keep CLAUDE.md short, and keep some weekly usage in reserve for deadlines. You can buy extra usage if you run out."},
 {t:"Network access", d:"This environment's network policy blocked many sites during research (Upwork, Etsy, Wikipedia, the FTC). For scraping or auditing client sites, change Network access in the environment settings."},
 {t:"Safe client access", d:"Ask for the least access that works: collaborator or staff accounts (Shopify, WordPress), invitations to private GitHub repos, read-only exports. Never log in to a client's personal accounts (for LinkedIn work, send them the text to post), and ask them to remove your access when the job ends."},
 {t:"Secrets stay secret", d:"Never paste client passwords into chat. Use the environment's secrets settings and temporary accounts, and never commit keys to Git."},
 {t:"Clean up after each client", d:"Chats you don't delete stay in your history. Delete finished client sessions from claude.ai/code; Anthropic erases deleted chats from its systems within 30 days. Don't use thumbs ratings on client work."},
 {t:"Steer from your phone", d:"Cloud sessions keep running in the background, and Remote Control lets you follow and steer a session from your phone or another computer."}
];

var GLOSSARY = [
 ["API key", "A secret code that lets software use a service such as Claude and bills that usage to the key's owner."],
 ["ATS", "Applicant tracking system: software employers use to filter resumes by keywords."],
 ["Care plan or retainer", "A monthly fee for ongoing updates, monitoring and small fixes after a project."],
 ["Connects", "Upwork's credits for sending proposals, $0.15 each."],
 ["EDI", "Electronic data interchange: the file formats big retailers use for orders, shipping notices and invoices."],
 ["Escrow", "The platform holds the client's payment and releases it to you when the work is approved."],
 ["GeoJSON", "A standard file format for map shapes, such as farm plot outlines."],
 ["KYC", "\"Know your customer\": the identity checks platforms run before paying you."],
 ["MCP", "Model Context Protocol: the standard way to connect tools and data to AI assistants like Claude."],
 ["Merchant of record", "A checkout service that sells on your behalf and handles sales tax and VAT (Gumroad, Lemon Squeezy, Paddle)."],
 ["OCR", "Optical character recognition: turning scanned images into real, selectable text."],
 ["Pay-per-event", "Apify's pricing, where users pay each time your tool performs a counted action."],
 ["PLR", "\"Private label rights\" content bought for resale. Etsy bans reselling it."],
 ["Regression", "A bug where something that used to work breaks after a change."],
 ["Rotate keys", "Replace passwords or API keys with new ones so any old copies stop working."],
 ["Routine", "A Claude Code task that runs on a schedule in the cloud."],
 ["SBOM", "Software bill of materials: a list of every component inside a piece of software."],
 ["Skill", "A saved set of instructions and files that teaches Claude a repeatable task. Run it by typing its name after a slash."],
 ["Staging", "A private copy of a website or app where changes are tested before going live."],
 ["VPAT and ACR", "A VPAT is the standard form used to write an Accessibility Conformance Report (ACR) about a product."],
 ["W-8BEN", "A US tax form non-US people give to US platforms so US tax isn't withheld unnecessarily."],
 ["WCAG", "Web Content Accessibility Guidelines: the standard used to judge whether websites and documents are accessible."],
 ["White-label", "Work you do that another business sells under its own name."],
 ["CAN-SPAM, PECR, GDPR", "US, UK and EU rules on marketing messages and personal data."],
 ["ASN (856)", "Advance ship notice: the EDI message a supplier sends a retailer before a shipment arrives."],
 ["Backdrop", "A free content-management system forked from Drupal 7, so old Drupal 7 sites can upgrade to it easily."],
 ["Fork", "A separate project started from a copy of another project's code."],
 ["Microsoft Graph", "Microsoft's current interface for programs that read or send Microsoft 365 email and files."],
 ["NVDA and PAC", "A free screen reader (NVDA) and a free PDF accessibility checker (PAC), both for Windows."],
 ["PCI DSS and SAQ", "The card industry's security standard (PCI DSS) and the yearly self-assessment questionnaire (SAQ) small merchants fill in."],
 ["PCIP", "Publisher's cataloging-in-publication: library cataloging data printed on a self-published book's copyright page."],
 ["pyRevit and Dynamo", "Tools for writing automation scripts inside Autodesk Revit."],
 ["security.txt", "A small text file on a website that tells people where to report security problems."],
 ["SIG Lite and CAIQ", "Two common standard security questionnaires that big customers send to software vendors."],
 ["SOC 2", "An independent audit report on a company's security controls, often requested by business customers."]
];
