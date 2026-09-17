# RULE: Default Browser Tool Protocol

<RULE[agent_browser_default]>
- AUTOMATICALLY use agent-browser CLI (agent-browser open, agent-browser snapshot -i, agent-browser click @ref) as the DEFAULT PRIMARY tool for ANY browser task (opening links, UI inspection, form testing, web scraping, verifying local dev servers).
- NEVER prompt or ask the user to explicitly specify agent-browser.
- Use Playwright (npx playwright test) ONLY for formal test suite files.
- Use browser_subagent ONLY when the user explicitly requests a WebP video recording artifact.
</RULE[agent_browser_default]>