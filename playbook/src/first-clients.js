// Where a newcomer with zero reviews actually finds first clients, ranked (research, Oct 2026).
var CHANNELS = [
 {name:"People you know, and the people they know",
  what:"Message 20–40 former classmates, former coworkers and owners of shops you use. Ask for introductions as well as work.",
  why:"Trust passes through someone they already know. A LinkedIn study of about 20 million people found that ties with roughly 10 mutual connections led to more new jobs than close friends did.",
  cost:"$0", first:"1–3 weeks"},
 {name:"Show-first outreach to small businesses",
  what:"Make a quick sample for one specific business (a demo site, a one-page audit, a cleaned spreadsheet) and send it with a personal first line.",
  why:"The finished sample stands in for reviews: the owner sees their own result before paying. Small batches work better: lists under 50 get about 3× the replies of lists over 500.",
  cost:"$0", first:"2–6 weeks"},
 {name:"Reddit hiring communities",
  what:"r/forhire, r/freelance_forhire, r/slavelabour and r/DoneDirtCheap. Sort by New every day and reply within the first hours with one matching sample.",
  why:"Posters pick whoever replies fast with relevant proof. r/forhire gets about 33 posts a day and bans pay under $15/h; a 6-hour-old post already has 20–30 replies.",
  cost:"$0 (some need account age or karma)", first:"Days to 2 weeks"},
 {name:"Upwork, with a tight saved search",
  what:"Apply only to fresh jobs with few proposals from clients with a verified payment method. See the Upwork steps below.",
  why:"Escrow protects both sides, and first-time clients take more chances on newcomers. Expect about 1 reply per 10–20 proposals; only about 1 posting in 12 is marked entry level.",
  cost:"$25–45 per 50 proposals", first:"2–8 weeks"},
 {name:"Communities around one tool",
  what:"The n8n forum's Jobs category, Webflow's hiring board, and Facebook or Slack groups for agency owners. Help people for 30 minutes a day before you pitch.",
  why:"Helpful public answers are proof anyone can check, and the people there already pay for the tool.",
  cost:"$0", first:"2–6 weeks"},
 {name:"Fiverr",
  what:"Publish 2–4 related gigs and send your own prospects to them. See the Fiverr steps below.",
  why:"Buyers come to you, so a low entry price and strong samples can win first orders. Fiverr's AI matcher (Mira) mostly picks sellers who already have orders, so don't wait for it.",
  cost:"$0 (20% per order)", first:"2–6 weeks"},
 {name:"White-label work for agencies",
  what:"Pitch 20–40 web, marketing or automation agencies with 2–3 matching samples and offer a small paid test.",
  why:"The agency's brand carries the trust; they need someone who delivers without creating more management work. Agency work tends to repeat.",
  cost:"$0", first:"3–8 weeks"},
 {name:"Smaller marketplaces",
  what:"PeoplePerHour (15 free proposals a month), Freelancer.com (6 free bids a month), Workana, Legiit. Use Contra to bill clients you find yourself, since it charges you 0%.",
  why:"Same review problem as Upwork, but less competition in some niches.",
  cost:"$0 to start", first:"2–4+ weeks"}
];

var UPWORK_STEPS = [
 "Pick one narrow lane in the words buyers search for, such as \"Excel and Google Sheets automation\" or \"Python web scraping to CSV\". Upwork rejects generic data-entry, writing and assistant profiles as oversupplied.",
 "Write the profile for Upwork's AI matcher (Uma), which compares it with each job. Repeat clients' own words in your title, fill the skills list, put results in the first two lines, and add 3–5 samples labeled as samples. Since May 2026 each person has a single profile.",
 "If the profile is rejected, add samples, switch to a less crowded category and resubmit.",
 "Budget Connects: $0.15 each, 10 free a month, and 2–16 per proposal depending on the job (often 4–6), so 50 proposals cost about $25–45. Don't pay to boost proposals.",
 "Save a search: payment verified, fewer than 5 proposals, client has no hires, posted in the last hour. Leave out jobs that ask for a \"free test\". Turn on notifications; postings peak Monday to Thursday.",
 "Open each proposal by restating the deliverable, then link a small proof made for their post. A 60–90 second screen recording works well. Add a 3-step plan, a fixed price, a delivery date and one sharp question.",
 "Add 1–2 fixed-price offers to the Project Catalog, for example \"Clean and dedupe your spreadsheet (up to 10,000 rows), $40\".",
 "Deliver the first job early and ask for feedback. The Rising Talent badge lifts you in search. Upwork lists several requirements, including a complete, identity-verified profile, recent activity, at least $250 earned in the past 12 months and a high rating (4.8+); check its help page for the current list."
];

var FIVERR_STEPS = [
 "Measure competition: search the exact phrase a buyer would type and check how many services come up. Under about 500 is low competition. Make sure the top gigs have recent reviews, which proves demand.",
 "Create 2–4 closely related gigs rather than 7 unrelated ones.",
 "Price slightly below the market average, as Fiverr itself advises, with 3 packages that have clear limits (rows, pages, revisions).",
 "Use before-and-after images, a 20–60 second video, every tag and an FAQ.",
 "Launch when you can reply within hours. Use Out of Office instead of leaving messages unanswered.",
 "Send real prospects (never friends or family) to your gig link. Fiverr's AI matcher (Mira) mostly picks sellers who already have orders.",
 "Never have friends or family order to create reviews, and never offer anything for a review. Fiverr permanently bans \"feedback boosting\", and the US FTC can seek up to $53,088 per fake review.",
 "Level 1 needs, among other things, 60 days as a seller, at least 5 orders from 3 different clients, $400 earned, a 4.4+ rating, a Success Score of 5+ and replies to at least 80% of messages. Money clears 14 days after each order."
];

var PROOF_STEPS = [
 "Pick a type of business and a proof Claude can make in under 45 minutes: a one-page demo site, a one-page audit PDF with a short screen recording, or a messy spreadsheet turned into a clean dashboard.",
 "Find leads on Google Maps: businesses with 20+ reviews and no website or a broken one. Many have no email, so plan on WhatsApp, Instagram, a phone call or a visit.",
 "Label every demo \"Concept prepared for [business] by [you]. Not the official site.\" Use placeholder or licensed stock photos, share it privately as screenshots or an unlisted link, and put it live on their own domain only after they say yes.",
 "Check your country's marketing rules, then send by hand in batches of 10–50, each with a personal first line (such as their rating and number of reviews) and an opt-out line. Expect 3–8% replies, so about 50 contacts gives 2–4 conversations.",
 "Make the first step small: the demo is free, a pilot costs $50–300, and bigger jobs take a 50% deposit.",
 "Follow up twice within about 10 days, then stop."
];
