# How PitchScoop Uses Sponsor Tools

A simple, non-technical guide to how these tools power PitchScoop during the hackathon.

---

## What this page covers
- What each sponsor tool is in plain language
- How PitchScoop specifically uses it in our platform
- Why it makes the hackathon better for participants, judges, and organizers

---

## 🧠 Smart Data & Context

### Senso.ai — Our "Context Brain"
- What it is: A tool that reads documents and turns them into clean, structured information.
- How PitchScoop uses it: We feed Senso.ai the judging rubrics, event rules, and example winning pitches. It organizes this into a single, easy-to-use knowledge base for our analysis.
- Why it helps: Everyone gets consistent guidance. The AI that reviews pitches uses the exact same criteria judges use.

### Bright Data — Our Market Researcher
- What it is: Automated web research for news, competitors, and market trends.
- How PitchScoop uses it: When a team submits a pitch, we pull public info to understand the competitive landscape and market buzz around that idea.
- Why it helps: Teams get meaningful context (“who else is building this?”), and judges see uniqueness and potential more clearly.

### Apify — Our Web Scout
- What it is: A way to scan many websites and collect organized info.
- How PitchScoop uses it: We run focused crawls on startup directories and product launch sites to find similar products and patterns.
- Why it helps: Faster, fairer comparisons without manual digging.

### LlamaIndex — Our Memory and Search
- What it is: Smart search across documents.
- How PitchScoop uses it: We index pitch transcripts, mentor notes, and past winners so judges can quickly find similar pitches or examples.
- Why it helps: Judges make better, faster decisions with the right context at hand.

### TigerData — Our Progress Tracker
- What it is: A timeline of important stats.
- How PitchScoop uses it: We track things like practice score improvements, Q&A engagement, and timing across sessions.
- Why it helps: Teams can see improvement over the event, and organizers get live insights.

### Redis / RedisVL — Our Speed + Smarts
- What it is: Ultra-fast storage with smart similarity search.
- How PitchScoop uses it: We store key pitch data and AI “embeddings” so we can instantly surface similar ideas and power real-time leaderboards.
- Why it helps: Everything feels instant—scores, comparisons, and search.

---

## 🎤 Audio, AI, and Assistants

### Gladia — Our Transcription Studio
- What it is: Turns speech into text (accurately and quickly).
- How PitchScoop uses it: Every pitch is automatically transcribed so judges can review and compare without missing details.
- Why it helps: No more “what did they say?”—everything is captured.

### MiniMax — Our Virtual Judge Panel
- What it is: A platform for building specialized AI assistants.
- How PitchScoop uses it: We run AI “judges” tuned to different perspectives (business, technical, user experience) to provide initial, consistent evaluations.
- Why it helps: Gives every team a fair, consistent baseline before human judges add their insight.

### HoneyHive — Our AI Quality Monitor
- What it is: Oversight for AI quality.
- How PitchScoop uses it: We monitor our AI scoring to check for accuracy and fairness across teams and categories.
- Why it helps: Builds trust in scores and keeps the process fair.

### Qodo — Our Feedback Writer
- What it is: Automated, personalized report creation.
- How PitchScoop uses it: After your pitch, we generate a clear, friendly feedback report with strengths and specific suggestions for next steps.
- Why it helps: Actionable takeaways you can use immediately.

### Airia — Our Smart Help Desk
- What it is: A smart search tool that answers questions.
- How PitchScoop uses it: Participants can ask, “What do judges value most?” or “Which sponsor APIs fit mobile apps?” and get helpful answers from event resources.
- Why it helps: Less time hunting, more time building.

### Horizon3.ai — Our Security Check
- What it is: Automated safety scan for apps and code.
- How PitchScoop uses it: We scan the PitchScoop platform and, with consent, team demos, to catch common security issues.
- Why it helps: Smooth demos and safer apps.

---

## 🔐 Access & Integration

### Stytch — Our Easy Sign-In
- What it is: Password-free, secure login.
- How PitchScoop uses it: Participants and judges join with a magic link sent to email—fast and secure.
- Why it helps: No account hassles, just click and go.

### Speakeasy — Our Integration Helper
- What it is: Makes it simple to connect to PitchScoop’s API.
- How PitchScoop uses it: We provide ready-made SDKs so teams can submit pitches and fetch feedback from their own projects if they’d like.
- Why it helps: Cuts setup time from hours to minutes.

---

## 🧩 How it all fits together (Pitch Day)
1) You sign in with a magic link (Stytch)
2) You present—your talk becomes text automatically (Gladia)
3) Our AI judges do a first pass (MiniMax) and are monitored for quality (HoneyHive)
4) We enrich context with market research (Bright Data, Apify) and organized rules (Senso.ai)
5) We store and search everything quickly (Redis/RedisVL, LlamaIndex)
6) We track improvements and engagement (TigerData)
7) You receive a friendly, personalized report (Qodo)
8) We keep things safe (Horizon3.ai)

---

## What this means for you
- Participants: Clear guidance, fast feedback, and helpful reports
- Judges: Accurate transcripts, quick comparisons, and better context
- Organizers: Live insights, smooth operations, and happy teams

---

If you remember one thing: PitchScoop uses these sponsor tools to make your experience faster, fairer, and more helpful—so you can focus on building something awesome.
