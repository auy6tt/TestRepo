var PLAN = [
 {title:"Week 1: set up and make proof", days:"Days 1–7", goal:"By day 7 you have one clear offer, three samples and working accounts.", items:[
  "Pick one main offer from \"Start here\" and one paid-on-results path to run alongside it.",
  "Turn off model training in Claude's privacy settings before you touch anyone else's files.",
  "Finish two free Claude Academy courses (academy.claude.com) and add the certificates to your profiles.",
  "Ask Claude to build three samples in this repo using made-up businesses or public data: a demo site for a fictional café, a messy spreadsheet fixed with a dashboard, and a PDF turned into a clean Excel file.",
  "Put the samples online (Cloudflare Pages or GitHub) and write a short case study for each: the problem, what you did, the result.",
  "Open accounts: Fiverr, Upwork, Contra, GitHub, and a payout method that works in your country (Payoneer, Wise or PayPal)."
 ]},
 {title:"Week 2: first conversations", days:"Days 8–14", goal:"At least 40 people or businesses have seen your offer.", items:[
  "Message 20 people you know: one sentence on what you do, plus 3 discounted pilot jobs in exchange for an honest testimonial.",
  "Publish 2 Fiverr gigs in narrow niches, with your samples as the gig images.",
  "Finish your Upwork profile with a niche headline. Send 10 tailored proposals, only to jobs under 1 hour old with fewer than 5 proposals.",
  "List 15 local businesses with no website from Google Maps. Build demos for the best 3 and show them in person or by message.",
  "Post one [For Hire] message on r/forhire with your samples and fixed starting prices."
 ]},
 {title:"Week 3: deliver and collect proof", days:"Days 15–21", goal:"First paid job delivered and a first review or testimonial in hand.", items:[
  "Deliver every pilot job early, with a short screen recording that explains what you did.",
  "Ask each happy client for a review or written testimonial on the day you deliver.",
  "Turn each job into a before-and-after case study (with the client's permission).",
  "Keep the rhythm: 10 proposals and 10 outreach messages this week.",
  "Try one paid-on-results path: enter an online hackathon, or claim an Expensify issue you can actually finish."
 ]},
 {title:"Week 4: repeat what worked and raise prices", days:"Days 22–30", goal:"One repeatable offer, a higher price and a monthly add-on.", items:[
  "Count the month: messages sent, replies, calls, wins. Keep the channel with the best reply rate and drop the worst.",
  "Raise prices about 20–30% after your first 3–5 reviews.",
  "Add a monthly care plan or retainer to every delivered project.",
  "Save your best proposal, intake form and delivery checklist as templates in this repo.",
  "Set next month's targets: messages per week, and one new sample in your niche."
 ]}
];

var TEMPLATES = [
 {file:"warm-network-message", title:"Message to people you know", use:"Send to 20 friends, relatives, classmates or coworkers in week 2.",
  text:"Hi [name], quick one. I've started doing [spreadsheet fixes / simple websites / resume rewrites] for small businesses and job seekers.\n\nI'm taking 3 pilot jobs at half price this month in exchange for honest feedback.\n\nDo you, or anyone you know, have [a messy spreadsheet / a business without a website / a resume that needs work]?\n\nHere's an example of what I do: [link]\n\nThanks!\n[Your name]"},
 {file:"show-first-local-business", title:"Show-first message to a local business", use:"Send with screenshots or an unlisted demo link after you've built their draft site.",
  text:"Hi [owner's name],\n\nI noticed [business name] doesn't have a website, so people who find you on Google only see your map listing.\n\nI made a free draft of what a simple site for you could look like: [unlisted link or screenshots]. It shows your hours, services and a tap-to-call button, and it works well on phones.\n\nIf you like it, I can put it live on your own domain this week for [price], and keep it updated for [monthly price] a month. If not, no problem, I'll delete the draft.\n\n[Your name]\n[Phone number]"},
 {file:"upwork-proposal", title:"Upwork proposal", use:"Under 150 words. Use the client's own words in the first line and answer what they asked.",
  text:"Hi [client name],\n\nYou need [their problem in one line, in their words].\n\nI did something similar here: [link to sample] ([one-line result]).\n\nHow I'd handle yours:\n1. [first step]\n2. [second step]\n3. [how you'll deliver it and check that it works]\n\nI can deliver by [date] for [fixed price]. I use AI tools to work faster and I check every result by hand.\n\nOne question so I can quote accurately: [a specific question about their job]?\n\n[Your name]"},
 {file:"fiverr-gig-spreadsheets", title:"Fiverr gig: spreadsheet fixes", use:"Gig title, description and three packages. Use screenshots of your samples as gig images.",
  text:"Title: I will fix your Excel or Google Sheets formulas and automate your report\n\nBroken formulas? Rebuilding the same report every week? Send me your file and tell me what it should do.\n\nWhat you get:\n- Formulas fixed and explained in plain language\n- Lookups, pivot tables and a summary tab\n- A check total so you can trust the numbers\n- Optional: an Apps Script or VBA macro to automate the boring part\n\nHow it works: send the file (remove anything you don't want me to see), I confirm scope and price before starting, and you get the file back with a short explanation.\n\nI use AI tools to work faster and I check every formula by hand.\n\nBasic, $30: fix up to 5 formulas\nStandard, $90: cleanup plus a summary or dashboard tab\nPremium, $200: automation script plus a walkthrough video"},
 {file:"reddit-for-hire", title:"Reddit [For Hire] post", use:"For r/forhire. Read the subreddit's posting rules first.",
  text:"[For Hire] Spreadsheet fixes, PDF to Excel, simple business websites. Fixed prices, samples inside\n\nI fix Excel and Google Sheets problems, turn PDFs into clean spreadsheets, and build simple one-page websites for small businesses.\n\nSamples:\n- [link 1]\n- [link 2]\n- [link 3]\n\nPrices: spreadsheet fixes from $30, PDF conversion from $20, one-page websites from $300.\n\nFor jobs under $50 you can pay after you've seen the result. Bigger jobs are 50% upfront.\n\nDM me what you need and I'll reply with a fixed quote."},
 {file:"app-rescue-offer", title:"Offer to fix a stuck AI-built app", use:"Reply to someone who posted that their Lovable, Bolt or Replit app is broken.",
  text:"Hi [name], I saw your post about [the problem] in your [Lovable / Bolt / Replit] app.\n\nI can do a fixed-price diagnosis: I'll reproduce the problem, find the cause and send you a short report with a fix plan within 24 hours, for $[50–99]. If you then want me to fix it, the diagnosis fee comes off the fix price.\n\nI only need read access to your code. I never need your production passwords.\n\n[Your name]"},
 {file:"testimonial-request", title:"Asking for a review or testimonial", use:"Send on delivery day, while the client is happiest.",
  text:"Thanks again for working with me on [project].\n\nIf you're happy with it, would you write 2–3 sentences about what I did and how it helped? I'd like to show it on my profile with your first name and business name.\n\nIf anything isn't right, tell me first and I'll fix it."},
 {file:"simple-agreement", title:"One-page agreement", use:"Fill in and get a written \"yes\" before starting any job off-platform. Not legal advice; adapt it to your country.",
  text:"Agreement between [client] and [you], [date]\n\nWork: [specific deliverables]\nNot included: [what's out of scope]\nDone when: [acceptance test, e.g. 3 pages load on phone and desktop, contact button works]\n\nPrice: [amount]. 50% before starting, 50% on delivery.\nRevisions: 2 rounds included, then [rate] per hour.\nTimeline: delivered by [date] if I receive [materials] by [date].\n\nOwnership: the final work is yours once fully paid. I may show it in my portfolio unless you say no.\nTools: I use AI tools to help with the work and review everything myself. I won't share your data beyond the tools this job needs.\nAccounts: domains, hosting and API keys stay in your name.\nLiability: limited to the amount paid for this work.\n\nAgreed: [client name, date]   [your name, date]"},
 {file:"website-intake", title:"Website intake questions", use:"Send after a yes, before building the live version.",
  text:"1. Business name, and what you sell in one sentence\n2. Area you serve and opening hours\n3. Phone and WhatsApp number to show\n4. 3–6 photos you own (or permission to use the ones on your Google listing)\n5. Your top 3 services, with prices if you want them shown\n6. Two websites you like the look of\n7. Do you already own a domain name? If yes, which?\n8. Who should I contact for future updates?"}
];
