var PLAN = [
 {title:"Week 1: build proof from nothing", days:"Days 1–7", goal:"By day 7 you have one clear offer, 3–5 samples written up as case studies, and accounts ready.", items:[
  "Day 1: pick one main offer from \"Start here\" and write it as one sentence, such as \"I turn messy sales spreadsheets into clean, auto-updating dashboards in 48 hours.\"",
  "Turn off model training in Claude's privacy settings before you touch anyone else's files.",
  "Days 2–4: ask Claude to build 3–5 samples in this repo from made-up or public data, each labeled as a self-initiated sample.",
  "Day 5: write each sample up as a case study (problem, process, solution, result) with real numbers, and publish them together on one page.",
  "Finish two free Claude Academy courses (academy.claude.com) and add the certificates to your profiles.",
  "Open accounts: Upwork (profile in clients' own words), Fiverr, Contra, GitHub, and a payout method that works in your country (PayPal, Payoneer or Wise).",
  "Start earning Reddit karma by answering questions in a help community such as r/excel. Hiring subreddits often require karma before you can post."
 ]},
 {title:"Week 2: first conversations", days:"Days 8–14", goal:"At least 50 people or businesses have seen a sample of your work.", items:[
  "Message 20–40 people you know, including former classmates, former coworkers and shop owners. Say what you do, and ask for introductions as well as work.",
  "Find 30 local businesses on Google Maps with 20+ reviews and no website. Build demos for the best 5 and send them in a batch, each with a personal first line.",
  "On Upwork, set up the saved search from \"First clients\" and send 10 proposals, each linking a small proof made for that post.",
  "Publish 2–4 related Fiverr gigs priced slightly below the average, with your samples as the gig images.",
  "Post a [For Hire] ad on r/forhire and r/freelance_forhire, then check new posts there every day."
 ]},
 {title:"Week 3: deliver and collect proof", days:"Days 15–21", goal:"First paid job delivered and a first review or testimonial in hand.", items:[
  "Deliver every job early, with a 60–90 second screen recording that explains what you did.",
  "Ask happy clients for a review or a written testimonial on delivery day.",
  "Follow up once with everyone who hasn't replied from week 2.",
  "Pitch 10 small agencies for white-label overflow work, offering a small paid test.",
  "Keep the rhythm: 10 proposals and 10 outreach messages this week.",
  "Enter one small online hackathon, or post a proposal on an Expensify \"Help Wanted\" issue you can actually finish."
 ]},
 {title:"Week 4: keep what worked and raise prices", days:"Days 22–30", goal:"One repeatable offer, a higher price and a monthly add-on.", items:[
  "Count the month: messages sent, replies, calls, wins. Keep the channel with the best reply rate and drop the worst.",
  "Raise prices about 20–30% once you have 3–5 reviews.",
  "Offer a monthly care plan or retainer with every delivered project.",
  "Turn each finished job into a before-and-after case study, with the client's permission.",
  "Save your best proposal, intake form and delivery checklist as templates in this repo.",
  "Set next month's targets: messages per week, and one new sample in your niche."
 ]}
];

var TEMPLATES = [
 {file:"warm-network-message", title:"Message to people you know", use:"Send to 20–40 former classmates, coworkers and shop owners in week 2. Asking for introductions matters as much as asking for work.",
  text:"Hey [name], hope [their new job / course / shop] is going well!\n\nI've started doing [spreadsheet clean-ups and small automations / simple websites] for small businesses. I'm doing my first 3 projects at a reduced price while I build my portfolio.\n\nDo you know anyone who's drowning in [messy Excel files / running a business without a decent website]? An introduction would mean a lot.\n\nHere's an example of what I do: [link]\n\nThanks!\n[Your name]"},
 {file:"show-first-local-business", title:"Show-first message to a local business", use:"Send by WhatsApp, Instagram or email with screenshots or an unlisted demo link, after you've built their concept site. Or say it in person.",
  text:"Hi [owner's name], I'm [your name], and I build websites for small businesses here in [city].\n\n[Business name] has [143] Google reviews at [4.8] stars but no website, so people searching \"[service] near me\" end up on other businesses' pages.\n\nI made you a free one-page concept from your public info: [screenshots or unlisted link]. Here's a 60-second walkthrough: [video link]. It's marked as a concept, not your official site.\n\nIf you like it, I can put it live on your own domain this week for [price], with 2 rounds of changes included. If not, there's no charge and I'll delete it.\n\nWorth a quick look?\n[Your name], [phone number]"},
 {file:"upwork-proposal", title:"Upwork proposal", use:"Under 150 words. Restate the deliverable in their words, then show a small proof made for this post.",
  text:"Hi [client name],\n\nYou need [the deliverable, in their words].\n\nI made a quick example for your post: [link to a 60–90 second screen recording or a sample file]. Similar finished work: [portfolio link].\n\nHow I'd do yours:\n1. [first step]\n2. [second step]\n3. [how you'll deliver it and check that it works]\n\nI can deliver by [date] for [fixed price]. I use AI tools to work faster and I check every result by hand.\n\nOne question so I can quote accurately: [a specific question about their job]?\n\n[Your name]"},
 {file:"fiverr-gig-spreadsheets", title:"Fiverr gig: spreadsheet fixes", use:"Gig title, description and three packages. Use screenshots of your samples as gig images.",
  text:"Title: I will fix your Excel or Google Sheets formulas and automate your report\n\nBroken formulas? Rebuilding the same report every week? Send me your file and tell me what it should do.\n\nWhat you get:\n- Formulas fixed and explained in plain language\n- Lookups, pivot tables and a summary tab\n- A check total so you can trust the numbers\n- Optional: an Apps Script or VBA macro to automate the boring part\n\nHow it works: send the file (remove anything you don't want me to see), I confirm scope and price before starting, and you get the file back with a short explanation.\n\nI use AI tools to work faster and I check every formula by hand.\n\nBasic, $30: fix up to 5 formulas\nStandard, $90: cleanup plus a summary or dashboard tab\nPremium, $200: automation script plus a walkthrough video"},
 {file:"reddit-for-hire", title:"Reddit [For Hire] post", use:"For r/forhire (one post a week, $15/hour minimum) and r/freelance_forhire. Read each community's rules first.",
  text:"[For Hire] Spreadsheet fixes, PDF to Excel, simple business websites. Fixed prices, samples inside\n\nI fix Excel and Google Sheets problems, turn PDFs into clean spreadsheets, and build simple one-page websites for small businesses.\n\nSamples:\n- [link 1]\n- [link 2]\n- [link 3]\n\nPrices: spreadsheet fixes from $30, PDF conversion from $20, one-page websites from $300.\n\nFor jobs under $50 you can pay after you've seen the result. Bigger jobs are 50% upfront.\n\nSend me a message with what you need and I'll reply with a fixed quote."},
 {file:"agency-white-label-pitch", title:"White-label pitch to an agency", use:"Email or LinkedIn message to small web, marketing or automation agencies. On LinkedIn, connect first and pitch after they accept.",
  text:"Hi [name],\n\nI saw [agency] builds [websites / automations] for [dentists / restaurants / their niche]. I build [landing pages / spreadsheet and n8n automations], and I'm happy to work white-label under your brand.\n\nTwo relevant samples: [link], [link]\n\nI have about [15] hours a week in [time zone], and small jobs are usually done in 48 hours. If you get overflow, a small paid test, such as one landing page for [price], would let you judge my quality and speed without risk.\n\nCan I send you my details to keep on file?\n\n[Your name]"},
 {file:"app-rescue-offer", title:"Offer to fix a stuck AI-built app", use:"Reply to someone who posted that their Lovable, Bolt or Replit app is broken.",
  text:"Hi [name], I saw your post about [the problem] in your [Lovable / Bolt / Replit] app.\n\nI can do a fixed-price diagnosis: I'll reproduce the problem, find the cause and send you a short report with a fix plan within 24 hours, for $[50–99]. If you then want me to fix it, the diagnosis fee comes off the fix price.\n\nI only need read access to your code. I never need your production passwords.\n\n[Your name]"},
 {file:"testimonial-request", title:"Asking for a review or testimonial", use:"Send on delivery day. Never offer anything in return for a positive review.",
  text:"Thanks again for working with me on [project].\n\nIf you're happy with it, would you write 2–3 sentences about what I did and how it helped? I'd like to show it on my profile with your first name and business name.\n\nIf anything isn't right, tell me first and I'll fix it."},
 {file:"simple-agreement", title:"One-page agreement", use:"Fill in and get a written \"yes\" before starting any job off-platform. Not legal advice; adapt it to your country.",
  text:"Agreement between [client] and [you], [date]\n\nWork: [specific deliverables]\nNot included: [what's out of scope]\nDone when: [acceptance test, e.g. 3 pages load on phone and desktop, contact button works]\n\nPrice: [amount]. 50% before starting, 50% on delivery.\nRevisions: 2 rounds included, then [rate] per hour.\nTimeline: delivered by [date] if I receive [materials] by [date].\n\nOwnership: the final work is yours once fully paid. I may show it in my portfolio unless you say no.\nTools: I use AI tools to help with the work and review everything myself. I won't share your data beyond the tools this job needs.\nAccounts: domains, hosting and API keys stay in your name.\nLiability: limited to the amount paid for this work.\n\nAgreed: [client name, date]   [your name, date]"},
 {file:"website-intake", title:"Website intake questions", use:"Send after a yes, before building the live version.",
  text:"1. Business name, and what you sell in one sentence\n2. Area you serve and opening hours\n3. Phone and WhatsApp number to show\n4. 3–6 photos you own (or permission to use the ones on your Google listing)\n5. Your top 3 services, with prices if you want them shown\n6. Two websites you like the look of\n7. Do you already own a domain name? If yes, which?\n8. Who should I contact for future updates?"}
];
