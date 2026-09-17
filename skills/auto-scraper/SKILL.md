---
name: auto-scraper
description: >-
  Autonomous Multi-Tier Web Scraping & Extraction System.
  Automatically selects the fastest, most token-efficient scraping engine
  (Tier 1: Direct HTTP -> Tier 2: agent-browser CLI -> Tier 3: Playwright -> Tier 4: browser_subagent)
  without requiring user instruction.
---

# Autonomous Multi-Tier Web Scraping Engine (`auto-scraper`)

## Core Protocol: Agent Autonomous Tier Selection

When a user asks to scrape, summarize, extract, or test any web page or site, **the agent MUST automatically determine and execute the most token-efficient engine** using the decision tree below:

```text
Target URL Request
  │
  ├─ 1. Static HTML / Documentation / Plain Article / API endpoint?
  │    └── Execute Tier 1: node C:\Users\advdi\.gemini\config\skills\auto-scraper\auto-scrape.js <url>
  │        (Direct HTTP fetch, ~50ms, zero browser overhead, lowest token cost)
  │
  ├─ 2. Client-Side Rendered SPA / Dynamic JavaScript / Interactive Page?
  │    └── Execute Tier 2: agent-browser CLI
  │        agent-browser open "<url>"; agent-browser snapshot -i (or agent-browser get text)
  │        (Daemonized Chromium, ~300ms, concise @e1 element refs, 90% token savings)
  │
  ├─ 3. Complex Multi-Step Form / Paginated Scraper / Auth Session required?
  │    └── Execute Tier 3: Programmatic Playwright / Puppeteer Script
  │        Execute headless Python/Node script via Playwright (0 runtime LLM tokens)
  │
  └─ 4. CAPTCHA / Complex Visual Human-in-the-Loop Reasoning needed?
       └── Execute Tier 4: Built-in browser_subagent
           Launch subagent tool for visual session recording and interactive solving
```

---

## 1. CLI Execution Reference

### Automated Multi-Tier Script:
```powershell
node C:\Users\advdi\.gemini\config\skills\auto-scraper\auto-scrape.js <url>
```
- **Text output only**: `node C:\Users\advdi\.gemini\config\skills\auto-scraper\auto-scrape.js --text <url>`
- **Structured JSON output**: `node C:\Users\advdi\.gemini\config\skills\auto-scraper\auto-scrape.js --json <url>`
- **Interactive Snapshot**: `node C:\Users\advdi\.gemini\config\skills\auto-scraper\auto-scrape.js --snapshot <url>`
- **Force specific tier**: `node C:\Users\advdi\.gemini\config\skills\auto-scraper\auto-scrape.js --tier 1 <url>`

---

## 2. Capability & Rules Matrix

1. **Default to Lowest Tokens**: Never launch a full browser subagent when a single `auto-scrape.js` call or `agent-browser get text` can fulfill the request.
2. **Interactive Form Filling**: Use `agent-browser fill '@e1' 'query'; agent-browser click '@e2'` for quick interactive commands.
3. **High Volume Scraping**: For pagination across >10 pages, generate a local Playwright script (`py` or `node`) to run headless with zero LLM loop overhead.
