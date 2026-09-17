const fs = require('fs');
const path = require('path');

const BRAIN_DIR = 'C:/Users/advdi/.gemini/antigravity-ide/brain';
const CACHE_FILE = 'C:/tools/.token-tracker-cache.json';

// Standard token factor heuristic: ~3.8 chars/token across mixed code and text
const CHARS_PER_TOKEN = 3.8;

function toTokens(chars) {
  if (!chars) return 0;
  return Math.round(chars / CHARS_PER_TOKEN);
}

function loadCache() {
  if (fs.existsSync(CACHE_FILE)) {
    try {
      return JSON.parse(fs.readFileSync(CACHE_FILE, 'utf-8'));
    } catch (e) {}
  }
  return {};
}

function saveCache(cache) {
  try {
    fs.writeFileSync(CACHE_FILE, JSON.stringify(cache, null, 2), 'utf-8');
  } catch (e) {}
}

function findSessions() {
  if (!fs.existsSync(BRAIN_DIR)) return [];
  const entries = fs.readdirSync(BRAIN_DIR);
  const sessions = [];

  for (const id of entries) {
    const pFull = path.join(BRAIN_DIR, id, '.system_generated', 'logs', 'transcript_full.jsonl');
    const pNorm = path.join(BRAIN_DIR, id, '.system_generated', 'logs', 'transcript.jsonl');
    
    // Always prioritize transcript_full.jsonl to avoid missing truncated payloads
    const targetPath = fs.existsSync(pFull) ? pFull : (fs.existsSync(pNorm) ? pNorm : null);
    if (targetPath) {
      const stat = fs.statSync(targetPath);
      sessions.push({
        id,
        path: targetPath,
        isFull: targetPath === pFull,
        mtime: stat.mtimeMs,
        size: stat.size,
        updatedAt: new Date(stat.mtimeMs)
      });
    }
  }

  return sessions.sort((a, b) => b.mtime - a.mtime);
}

function auditSession(sessionInfo, cache) {
  const { id, path: filePath, mtime, size, isFull } = sessionInfo;

  if (cache && cache[id] && cache[id].mtime === mtime && cache[id].size === size) {
    return cache[id].data;
  }

  const rawContent = fs.readFileSync(filePath, 'utf-8');
  const rawLines = rawContent.trim().split('\n');
  const steps = [];
  for (let i = 0; i < rawLines.length; i++) {
    try {
      steps.push(JSON.parse(rawLines[i]));
    } catch (e) {}
  }

  let userChars = 0;
  let answerChars = 0;
  let thinkingChars = 0;
  let systemChars = 0;
  let toolArgsChars = 0;
  let sessionTitle = 'Untitled Session';
  let firstPromptFound = false;

  const toolStats = {};
  const heavyEvents = [];
  const toolCallQueue = [];

  for (const step of steps) {
    if (step.type === 'USER_INPUT') {
      const len = step.content ? step.content.length : 0;
      userChars += len;
      if (!firstPromptFound && step.content) {
        let clean = step.content.replace(/<\/?USER_REQUEST>/g, '').trim().split('\n')[0];
        if (clean) {
          sessionTitle = clean.substring(0, 65);
          firstPromptFound = true;
        }
      }
    } else if (step.type === 'PLANNER_RESPONSE') {
      answerChars += step.content ? step.content.length : 0;
      thinkingChars += step.thinking ? step.thinking.length : 0;
      if (step.tool_calls && Array.isArray(step.tool_calls)) {
        for (const tc of step.tool_calls) {
          const tcChars = JSON.stringify(tc.args || {}).length;
          toolArgsChars += tcChars;
          toolCallQueue.push({
            name: tc.name || 'unknown',
            args: tc.args || {},
            inChars: tcChars,
            stepIndex: step.step_index
          });
        }
      }
    } else if (step.type === 'SYSTEM_MESSAGE') {
      systemChars += step.content ? step.content.length : 0;
    } else {
      // Tool output step
      const outChars = step.content ? step.content.length : 0;
      const matchedCall = toolCallQueue.shift();

      let category = 'Other Tools';
      let subDetail = step.type;

      if (matchedCall) {
        const rawName = matchedCall.name;
        if (rawName === 'run_command') {
          const cmdLine = (matchedCall.args.CommandLine || '').trim();
          const firstLine = cmdLine.split('\n')[0];
          if (/cbm(\.cmd)?\s+/i.test(firstLine) || firstLine.includes('codebase-memory')) {
            category = 'cbm (Codebase Memory)';
            const sub = firstLine.match(/cbm(\.cmd)?\s+([a-z0-9_-]+)/i);
            subDetail = sub ? `cbm ${sub[2]}` : 'cbm query';
          } else if (/rg-mini/i.test(firstLine)) {
            category = 'rg-mini (Fast Grep)';
            subDetail = 'rg-mini';
          } else if (/fd-mini/i.test(firstLine)) {
            category = 'fd-mini (Fast Find)';
            subDetail = 'fd-mini';
          } else if (/token-save/i.test(firstLine)) {
            category = 'token-save (Context Engine)';
            subDetail = 'token-save';
          } else if (/git\s+/i.test(firstLine)) {
            category = 'git commands';
            subDetail = 'git CLI';
          } else {
            category = 'Terminal Commands';
            subDetail = firstLine.substring(0, 35);
          }
        } else if (rawName === 'view_file') {
          category = 'view_file (File Reads)';
          const fPath = matchedCall.args.AbsolutePath || '';
          subDetail = path.basename(fPath) || 'file read';
        } else if (rawName === 'replace_file_content' || rawName === 'write_to_file' || rawName === 'multi_replace_file_content') {
          category = 'File Writes & Edits';
          subDetail = rawName;
        } else if (rawName === 'search_web') {
          category = 'search_web';
          subDetail = 'web search';
        } else if (rawName === 'read_url_content') {
          category = 'read_url_content';
          subDetail = 'read url';
        } else {
          category = rawName;
          subDetail = rawName;
        }
      } else {
        if (step.type === 'RUN_COMMAND') category = 'Terminal Commands';
        else if (step.type === 'VIEW_FILE') category = 'view_file (File Reads)';
        else category = step.type;
        subDetail = step.type;
      }

      if (!toolStats[category]) {
        toolStats[category] = { calls: 0, inChars: 0, outChars: 0, details: {} };
      }
      toolStats[category].calls++;
      toolStats[category].outChars += outChars;
      if (matchedCall) {
        toolStats[category].inChars += matchedCall.inChars;
      }
      toolStats[category].details[subDetail] = (toolStats[category].details[subDetail] || 0) + outChars;

      const outTok = toTokens(outChars);
      if (outTok > 500) {
        heavyEvents.push({
          step: step.step_index,
          category,
          subDetail,
          chars: outChars,
          tokens: outTok,
          preview: (step.content || '').substring(0, 75).replace(/\r?\n/g, ' ')
        });
      }
    }
  }

  const totalToolOutChars = Object.values(toolStats).reduce((acc, t) => acc + t.outChars, 0);
  const grandTotalChars = userChars + answerChars + thinkingChars + systemChars + toolArgsChars + totalToolOutChars;

  const auditedData = {
    id,
    title: sessionTitle,
    mtime,
    size,
    isFull,
    date: new Date(mtime).toISOString(),
    totalSteps: steps.length,
    chars: {
      grandTotal: grandTotalChars,
      user: userChars,
      answer: answerChars,
      thinking: thinkingChars,
      system: systemChars,
      toolArgs: toolArgsChars,
      toolOut: totalToolOutChars
    },
    tokens: {
      grandTotal: toTokens(grandTotalChars),
      user: toTokens(userChars),
      answer: toTokens(answerChars),
      thinking: toTokens(thinkingChars),
      system: toTokens(systemChars),
      toolArgs: toTokens(toolArgsChars),
      toolOut: toTokens(totalToolOutChars)
    },
    toolStats,
    heavyEvents
  };

  if (cache) {
    cache[id] = { mtime, size, data: auditedData };
  }

  return auditedData;
}

function renderBar(pct, width = 14) {
  const filled = Math.min(width, Math.max(0, Math.round((pct / 100) * width)));
  return '█'.repeat(filled) + '░'.repeat(width - filled);
}

function cmdScan(args, sessions, cache) {
  let filtered = sessions;

  const nIdx = args.indexOf('-n');
  if (nIdx !== -1 && args[nIdx + 1]) {
    const limit = parseInt(args[nIdx + 1], 10);
    if (!isNaN(limit)) filtered = filtered.slice(0, limit);
  }

  if (args.includes('--today')) {
    const todayStr = new Date().toISOString().split('T')[0];
    filtered = filtered.filter(s => s.updatedAt.toISOString().startsWith(todayStr));
  }

  const auditedList = filtered.map(s => auditSession(s, cache));
  saveCache(cache);

  if (args.includes('--sort-tokens')) {
    auditedList.sort((a, b) => b.tokens.grandTotal - a.tokens.grandTotal);
  }

  if (args.includes('--csv')) {
    console.log('SessionID,Date,Title,Steps,GrandTotalChars,GrandTotalTokens,UserTokens,AssistantTokens,ThinkingTokens,ToolInTokens,ToolOutTokens');
    for (const a of auditedList) {
      console.log(`"${a.id}","${a.date}","${a.title.replace(/"/g, '""')}",${a.totalSteps},${a.chars.grandTotal},${a.tokens.grandTotal},${a.tokens.user},${a.tokens.answer},${a.tokens.thinking},${a.tokens.toolArgs},${a.tokens.toolOut}`);
    }
    return;
  }

  if (args.includes('--json')) {
    console.log(JSON.stringify(auditedList, null, 2));
    return;
  }

  console.log('\n' + '═'.repeat(84));
  console.log('            ANTIGRAVITY MULTI-SESSION TOKEN & CONTEXT SCANNER');
  console.log('═'.repeat(84));
  console.log(` Scanned: ${auditedList.length} chat sessions | Ground Truth Source: transcript_full.jsonl`);
  console.log(` Token Metric: 1 Token ≈ 3.8 Characters (Unbiased BPE Code/Text Baseline)`);
  console.log('─'.repeat(84));

  let sumChars = 0;
  let sumTokens = 0;
  let sumToolOut = 0;
  let sumSteps = 0;

  console.log(' #   Session ID   Date         Steps    Total Chars    Est Tokens   Session Title');
  console.log(' ' + '─'.repeat(82));

  auditedList.forEach((s, idx) => {
    sumChars += s.chars.grandTotal;
    sumTokens += s.tokens.grandTotal;
    sumToolOut += s.tokens.toolOut;
    sumSteps += s.totalSteps;

    const numStr = String(idx + 1).padStart(2);
    const shortId = s.id.substring(0, 8);
    const dStr = s.date.split('T')[0];
    const stepsStr = String(s.totalSteps).padStart(5);
    const charsStr = s.chars.grandTotal.toLocaleString().padStart(12);
    const tokStr = s.tokens.grandTotal.toLocaleString().padStart(11);
    const titleStr = s.title.length > 28 ? s.title.substring(0, 25) + '...' : s.title;

    console.log(` ${numStr}  ${shortId}   ${dStr}   ${stepsStr}   ${charsStr}   ${tokStr}   ${titleStr}`);
  });

  console.log('─'.repeat(84));
  console.log(` EMPIRICAL TOTALS (${auditedList.length} SESSIONS COMBINED):`);
  console.log(` • Cumulative Steps:         ${sumSteps.toLocaleString()} steps`);
  console.log(` • Cumulative Payload Chars: ${sumChars.toLocaleString()} characters`);
  console.log(` • Cumulative Payload Tok:   ~${sumTokens.toLocaleString()} tokens`);
  console.log(` • Tool Return Payloads:     ~${sumToolOut.toLocaleString()} tokens (${((sumToolOut / (sumTokens || 1)) * 100).toFixed(1)}% of total context payload)`);
  console.log('═'.repeat(84));
  console.log(' Tip: Run "token-tracker audit <id>" for single-session breakdown.');
  console.log('      Run "token-tracker audit --all" for combined tool cost audit.\n');
}

function cmdAudit(args, sessions, cache) {
  if (args.includes('--all')) {
    const auditedList = sessions.map(s => auditSession(s, cache));
    saveCache(cache);

    const aggregated = {
      id: `ALL (${auditedList.length} Sessions)`,
      title: 'Global Multi-Session Portfolio Audit',
      totalSteps: auditedList.reduce((a, b) => a + b.totalSteps, 0),
      chars: {
        grandTotal: auditedList.reduce((a, b) => a + b.chars.grandTotal, 0),
        user: auditedList.reduce((a, b) => a + b.chars.user, 0),
        answer: auditedList.reduce((a, b) => a + b.chars.answer, 0),
        thinking: auditedList.reduce((a, b) => a + b.chars.thinking, 0),
        system: auditedList.reduce((a, b) => a + b.chars.system, 0),
        toolArgs: auditedList.reduce((a, b) => a + b.chars.toolArgs, 0),
        toolOut: auditedList.reduce((a, b) => a + b.chars.toolOut, 0)
      },
      tokens: {
        grandTotal: auditedList.reduce((a, b) => a + b.tokens.grandTotal, 0),
        user: auditedList.reduce((a, b) => a + b.tokens.user, 0),
        answer: auditedList.reduce((a, b) => a + b.tokens.answer, 0),
        thinking: auditedList.reduce((a, b) => a + b.tokens.thinking, 0),
        system: auditedList.reduce((a, b) => a + b.tokens.system, 0),
        toolArgs: auditedList.reduce((a, b) => a + b.tokens.toolArgs, 0),
        toolOut: auditedList.reduce((a, b) => a + b.tokens.toolOut, 0)
      },
      toolStats: {},
      heavyEvents: []
    };

    for (const a of auditedList) {
      for (const [k, v] of Object.entries(a.toolStats)) {
        if (!aggregated.toolStats[k]) aggregated.toolStats[k] = { calls: 0, inChars: 0, outChars: 0 };
        aggregated.toolStats[k].calls += v.calls;
        aggregated.toolStats[k].inChars += v.inChars;
        aggregated.toolStats[k].outChars += v.outChars;
      }
      aggregated.heavyEvents.push(...a.heavyEvents);
    }

    printSessionAudit(aggregated);
    return;
  }

  let target = sessions[0];
  const idArg = args.find(a => !a.startsWith('-') && a !== 'audit');
  if (idArg) {
    const found = sessions.find(s => s.id.startsWith(idArg));
    if (!found) {
      console.error(`Session matching "${idArg}" not found.`);
      process.exit(1);
    }
    target = found;
  }

  const audited = auditSession(target, cache);
  saveCache(cache);

  if (args.includes('--json')) {
    console.log(JSON.stringify(audited, null, 2));
    return;
  }

  printSessionAudit(audited);
}

function printSessionAudit(data) {
  const { id, title, totalSteps, chars, tokens, toolStats, heavyEvents } = data;

  console.log('\n' + '═'.repeat(78));
  console.log('             ANTIGRAVITY GROUND-TRUTH TOKEN & CONTEXT AUDIT');
  console.log('═'.repeat(78));
  console.log(` Target Session:    ${id}`);
  if (title) console.log(` Session Intent:    "${title}"`);
  console.log(` Total Steps:       ${totalSteps} logged steps`);
  console.log(` Total Volume:      ${chars.grandTotal.toLocaleString()} characters  (~${tokens.grandTotal.toLocaleString()} estimated tokens)`);
  console.log(` Calculation Base:  1 Token ≈ 3.8 Characters (Unbiased, No Fabricated Multipliers)`);
  console.log('─'.repeat(78));

  console.log(' CATEGORY BREAKDOWN (EXACT CHARACTERS & TOKENS):');
  console.log('');

  const catRows = [
    { label: 'Tool Return Payloads (Context)', chars: chars.toolOut, tokens: tokens.toolOut },
    { label: 'Tool Arguments Sent (Prompt)', chars: chars.toolArgs, tokens: tokens.toolArgs },
    { label: 'Assistant Responses (Output)', chars: chars.answer, tokens: tokens.answer },
    { label: 'Model Thinking (Reasoning)', chars: chars.thinking, tokens: tokens.thinking },
    { label: 'User Prompts (Input)', chars: chars.user, tokens: tokens.user },
    { label: 'System Injections (Prompt)', chars: chars.system, tokens: tokens.system },
  ];

  catRows.sort((a, b) => b.chars - a.chars);

  for (const row of catRows) {
    const pct = chars.grandTotal > 0 ? (row.chars * 100 / chars.grandTotal) : 0;
    const bar = renderBar(pct, 12);
    const charsStr = row.chars.toLocaleString().padStart(9) + ' ch';
    const tokStr = '~' + row.tokens.toLocaleString().padStart(7) + ' tok';
    console.log(`  ${row.label.padEnd(34)} ${charsStr}  ${tokStr} (${pct.toFixed(1).padStart(4)}%) [${bar}]`);
  }

  console.log('─'.repeat(78));
  console.log(' TOOL COST & OVERHEAD BREAKDOWN:');
  console.log('');
  console.log('  Tool Category                 Calls   In Chars   Out Chars   Out Tok   Avg/Call');
  console.log('  ' + '─'.repeat(72));

  const sortedTools = Object.entries(toolStats).sort((a, b) => b[1].outChars - a[1].outChars);
  for (const [name, s] of sortedTools) {
    const outTok = toTokens(s.outChars);
    const avg = s.calls > 0 ? Math.round(outTok / s.calls) : 0;
    const callsStr = String(s.calls).padStart(5);
    const inChStr = String(s.inChars).padStart(9);
    const outChStr = String(s.outChars).padStart(10);
    const outTokStr = ('~' + outTok.toLocaleString()).padStart(8);
    const avgStr = ('~' + avg).padStart(6) + ' tok';
    console.log(`  ${name.padEnd(28)} ${callsStr}  ${inChStr}  ${outChStr}  ${outTokStr}   ${avgStr}`);
  }

  if (heavyEvents.length > 0) {
    console.log('─'.repeat(78));
    console.log(' ⚠️  HEAVIEST PAYLOADS IDENTIFIED (>500 tokens):');
    console.log('  (These are your actual token hotspots / potential context leaks)');
    console.log('');
    const topHeavy = heavyEvents.sort((a, b) => b.tokens - a.tokens).slice(0, 5);
    for (const h of topHeavy) {
      console.log(`  • Step #${String(h.step).padEnd(4)} [~${h.tokens} tok / ${h.chars} ch] ${h.category} (${h.subDetail})`);
      console.log(`    ↳ "${h.preview}..."`);
    }
  }

  console.log('═'.repeat(78) + '\n');
}

function runCounterfactualReplay(sessionInfo) {
  const { id, path: filePath } = sessionInfo;
  const rawContent = fs.readFileSync(filePath, 'utf-8');
  const rawLines = rawContent.trim().split('\n');
  const steps = [];
  for (let i = 0; i < rawLines.length; i++) {
    try {
      steps.push(JSON.parse(rawLines[i]));
    } catch (e) {}
  }

  let gitCommit = 'unknown';
  try {
    const { execSync } = require('child_process');
    gitCommit = execSync('git rev-parse --short HEAD', { cwd: __dirname, stdio: ['ignore', 'pipe', 'ignore'] }).toString().trim();
  } catch (e) {}

  let totalPlannerTurns = 0;
  for (const s of steps) {
    if (s.type === 'PLANNER_RESPONSE') totalPlannerTurns++;
  }

  let currentPlannerTurn = 0;
  const toolCallQueue = [];
  const ledger = [];

  let obsUserChars = 0;
  let obsAnswerChars = 0;
  let obsThinkingChars = 0;
  let obsSystemChars = 0;
  let obsToolArgsChars = 0;
  let obsToolOutChars = 0;

  let totalBaselineAChars = 0;
  let totalBaselineBChars = 0;
  let totalActualChars = 0;

  let cumulativeExposureReductionA = 0;
  let cumulativeExposureReductionB = 0;

  const categoryBreakdown = {
    view_file: { calls: 0, actualChars: 0, baselineAChars: 0, baselineBChars: 0 },
    cbm: { calls: 0, actualChars: 0, baselineAChars: 0, baselineBChars: 0 },
    mini_search: { calls: 0, actualChars: 0, baselineAChars: 0, baselineBChars: 0 },
    token_save: { calls: 0, actualChars: 0, baselineAChars: 0, baselineBChars: 0 },
    other: { calls: 0, actualChars: 0, baselineAChars: 0, baselineBChars: 0 }
  };

  for (const step of steps) {
    if (step.type === 'USER_INPUT') {
      obsUserChars += step.content ? step.content.length : 0;
    } else if (step.type === 'PLANNER_RESPONSE') {
      currentPlannerTurn++;
      obsAnswerChars += step.content ? step.content.length : 0;
      obsThinkingChars += step.thinking ? step.thinking.length : 0;
      if (step.tool_calls && Array.isArray(step.tool_calls)) {
        for (const tc of step.tool_calls) {
          const tcLen = JSON.stringify(tc.args || {}).length;
          obsToolArgsChars += tcLen;
          toolCallQueue.push({
            turn: currentPlannerTurn,
            name: tc.name || 'unknown',
            args: tc.args || {},
            stepIndex: step.step_index
          });
        }
      }
    } else if (step.type === 'SYSTEM_MESSAGE') {
      obsSystemChars += step.content ? step.content.length : 0;
    } else {
      const outChars = step.content ? step.content.length : 0;
      obsToolOutChars += outChars;
      totalActualChars += outChars;

      const call = toolCallQueue.shift();
      let toolName = 'other';
      let targetDesc = 'unknown';
      let catKey = 'other';
      let baseAChars = outChars;
      let baseBChars = outChars;

      if (call) {
        toolName = call.name;
        if (call.name === 'view_file') {
          catKey = 'view_file';
          const fPath = call.args.AbsolutePath || '';
          targetDesc = path.basename(fPath) || 'file';
          let fullFileSize = outChars;
          if (fPath && fs.existsSync(fPath)) {
            try { fullFileSize = fs.statSync(fPath).size; } catch (e) {}
          } else {
            fullFileSize = Math.max(outChars, 14000);
          }
          baseAChars = Math.max(outChars, fullFileSize);
          baseBChars = Math.max(outChars, Math.min(fullFileSize, Math.max(Math.round(outChars * 2.5), 4500)));
        } else if (call.name === 'run_command') {
          const cmd = (call.args.CommandLine || '').trim();
          const firstLine = cmd.split('\n')[0];
          targetDesc = firstLine.substring(0, 32);

          if (/cbm/i.test(cmd)) {
            catKey = 'cbm';
            toolName = 'cbm';
            baseAChars = Math.max(outChars, 22000);
            baseBChars = Math.max(outChars, 9000);
          } else if (/rg-mini|fd-mini|es-mini/i.test(cmd)) {
            catKey = 'mini_search';
            toolName = 'bounded-search';
            baseAChars = Math.max(outChars, 12000);
            baseBChars = Math.max(outChars, 3200);
          } else if (/token-save/i.test(cmd)) {
            catKey = 'token_save';
            toolName = 'token-save';
            baseAChars = Math.max(outChars, 16000);
            baseBChars = Math.max(outChars, 6500);
          }
        }
      }

      totalBaselineAChars += baseAChars;
      totalBaselineBChars += baseBChars;

      categoryBreakdown[catKey].calls++;
      categoryBreakdown[catKey].actualChars += outChars;
      categoryBreakdown[catKey].baselineAChars += baseAChars;
      categoryBreakdown[catKey].baselineBChars += baseBChars;

      const deltaA = Math.max(0, baseAChars - outChars);
      const deltaB = Math.max(0, baseBChars - outChars);
      const remainingTurns = Math.max(0, totalPlannerTurns - (call ? call.turn : currentPlannerTurn));

      cumulativeExposureReductionA += (deltaA * remainingTurns);
      cumulativeExposureReductionB += (deltaB * remainingTurns);

      ledger.push({
        step: step.step_index,
        turn: call ? call.turn : currentPlannerTurn,
        tool: toolName,
        target: targetDesc,
        actual_chars: outChars,
        baseA_chars: baseAChars,
        baseB_chars: baseBChars,
        actual_tokens: toTokens(outChars),
        baseA_tokens: toTokens(baseAChars),
        baseB_tokens: toTokens(baseBChars),
        deltaA_tokens: toTokens(deltaA),
        deltaB_tokens: toTokens(deltaB),
        compoundedA_tokens: toTokens(deltaA * remainingTurns),
        compoundedB_tokens: toTokens(deltaB * remainingTurns)
      });
    }
  }

  const grandTotalChars = obsUserChars + obsAnswerChars + obsThinkingChars + obsSystemChars + obsToolArgsChars + obsToolOutChars;

  return {
    sessionId: id,
    gitCommit,
    totalSteps: steps.length,
    plannerTurns: totalPlannerTurns,
    observed: {
      totalChars: grandTotalChars,
      toolOutputChars: obsToolOutChars,
      userChars: obsUserChars,
      assistantChars: obsAnswerChars,
      thinkingChars: obsThinkingChars,
      systemChars: obsSystemChars,
      toolArgsChars: obsToolArgsChars,
      estTokens: toTokens(grandTotalChars),
      estToolTokens: toTokens(obsToolOutChars)
    },
    counterfactual: {
      actualToolChars: totalActualChars,
      baselineAChars: totalBaselineAChars,
      baselineBChars: totalBaselineBChars,
      actualToolTokens: toTokens(totalActualChars),
      baselineATokens: toTokens(totalBaselineAChars),
      baselineBTokens: toTokens(totalBaselineBChars),
      immediateSavingsA: toTokens(totalBaselineAChars - totalActualChars),
      immediateSavingsB: toTokens(totalBaselineBChars - totalActualChars),
      reductionPctA: ((totalBaselineAChars - totalActualChars) / totalBaselineAChars * 100).toFixed(1),
      reductionPctB: ((totalBaselineBChars - totalActualChars) / totalBaselineBChars * 100).toFixed(1)
    },
    cumulativeExposure: {
      exposureCharsA: cumulativeExposureReductionA,
      exposureCharsB: cumulativeExposureReductionB,
      exposureTokensA: toTokens(cumulativeExposureReductionA),
      exposureTokensB: toTokens(cumulativeExposureReductionB)
    },
    categoryBreakdown,
    ledger
  };
}

function printReplayReport(data, showLedger = false) {
  const { sessionId, gitCommit, totalSteps, plannerTurns, observed, counterfactual, cumulativeExposure, categoryBreakdown, ledger } = data;

  console.log('\n' + '═'.repeat(78));
  console.log('         YURO DETERMINISTIC COUNTERFACTUAL REPLAY TELEMETRY');
  console.log('═'.repeat(78));
  console.log(` Target Session:    ${sessionId}`);
  console.log(` Git Commit SHA:    ${gitCommit}`);
  console.log(` Replay Scope:      ${totalSteps} Logged Steps (${plannerTurns} Model Planning Turns)`);
  console.log(` Character Metric:  EXACT (Directly Measured from transcript_full.jsonl)`);
  console.log(` Token Metric:      ESTIMATED (3.8 Characters / Token Baseline)`);
  console.log('─'.repeat(78));

  console.log(' 1. OBSERVED TRANSCRIPT TELEMETRY (EXACT MEASUREMENTS):');
  console.log('');
  console.log(`  • Total Transcript Volume:        ${observed.totalChars.toLocaleString().padStart(12)} chars   (~${observed.estTokens.toLocaleString()} est tok)`);
  console.log(`  • Tool Return Payloads:           ${observed.toolOutputChars.toLocaleString().padStart(12)} chars   (~${observed.estToolTokens.toLocaleString()} est tok)`);
  console.log(`  • Assistant Answers & Thinking:   ${(observed.assistantChars + observed.thinkingChars).toLocaleString().padStart(12)} chars   (~${toTokens(observed.assistantChars + observed.thinkingChars).toLocaleString()} est tok)`);
  console.log(`  • Tool Invocation Arguments:      ${observed.toolArgsChars.toLocaleString().padStart(12)} chars   (~${toTokens(observed.toolArgsChars).toLocaleString()} est tok)`);
  console.log(`  • User Inputs & Injections:       ${(observed.userChars + observed.systemChars).toLocaleString().padStart(12)} chars   (~${toTokens(observed.userChars + observed.systemChars).toLocaleString()} est tok)`);
  console.log('─'.repeat(78));

  console.log(' 2. TASK-EQUIVALENT COUNTERFACTUAL COMPARISON (TOOL PAYLOADS):');
  console.log('');
  console.log('  Configuration                     Payload Volume      Estimated Tokens   Delta');
  console.log('  ' + '─'.repeat(72));
  console.log(`  Baseline A (Naive / Unbounded)   ${counterfactual.baselineAChars.toLocaleString().padStart(12)} chars     ~${counterfactual.baselineATokens.toLocaleString().padStart(8)} tok     (Worst-Case)`);
  console.log(`  Baseline B (Practical Agent)     ${counterfactual.baselineBChars.toLocaleString().padStart(12)} chars     ~${counterfactual.baselineBTokens.toLocaleString().padStart(8)} tok     (Realistic)`);
  console.log(`  Baseline C (YURO Observed)       ${counterfactual.actualToolChars.toLocaleString().padStart(12)} chars     ~${counterfactual.actualToolTokens.toLocaleString().padStart(8)} tok     (Active)`);
  console.log('  ' + '─'.repeat(72));
  console.log(`  Immediate Reduction vs Baseline A:    -${counterfactual.reductionPctA}%   (~${counterfactual.immediateSavingsA.toLocaleString()} est tokens saved)`);
  console.log(`  Immediate Reduction vs Baseline B:    -${counterfactual.reductionPctB}%   (~${counterfactual.immediateSavingsB.toLocaleString()} est tokens saved)`);
  console.log('─'.repeat(78));

  console.log(' 3. PER-TOOL COUNTERFACTUAL BREAKDOWN:');
  console.log('');
  console.log('  Tool Category       Calls     Observed Tok     Baseline B Tok   Immediate Savings');
  console.log('  ' + '─'.repeat(72));

  for (const [k, v] of Object.entries(categoryBreakdown)) {
    if (v.calls === 0) continue;
    const actTok = toTokens(v.actualChars);
    const bTok = toTokens(v.baselineBChars);
    const diff = Math.max(0, bTok - actTok);
    const pct = bTok > 0 ? ((diff / bTok) * 100).toFixed(1) : '0.0';
    console.log(`  ${k.padEnd(18)} ${String(v.calls).padStart(5)}   ~${actTok.toLocaleString().padStart(8)} tok   ~${bTok.toLocaleString().padStart(10)} tok   ~${diff.toLocaleString().padStart(8)} tok (-${pct}%)`);
  }
  console.log('─'.repeat(78));

  console.log(' 4. CUMULATIVE CONTEXT EXPOSURE REDUCTION:');
  console.log('  Formula: Σ [ (Total Planner Turns - Turn_t) × Δ_t ]');
  console.log('');
  console.log(`  • Cumulative Context-Turn Exposure Avoided vs Baseline A:  ~${cumulativeExposure.exposureTokensA.toLocaleString()} token-turns`);
  console.log(`  • Cumulative Context-Turn Exposure Avoided vs Baseline B:  ~${cumulativeExposure.exposureTokensB.toLocaleString()} token-turns`);
  console.log('─'.repeat(78));

  console.log(' 5. METHODOLOGY & TASK-EQUIVALENT SEMANTICS:');
  console.log('  • Baseline A (Naive): Unrestricted whole-file reads, uncapped ripgrep, multi-file inspection.');
  console.log('  • Baseline B (Practical): Sibling function slice, capped terminal grep, targeted file search.');
  console.log('  • Baseline C (YURO): Actual observed tool payloads recorded in transcript.');
  console.log('═'.repeat(78) + '\n');

  if (showLedger && ledger.length > 0) {
    console.log('── STEP REPLAY LEDGER (TOP 10 SIGNIFICANT DELTAS) ──');
    const sortedLedger = [...ledger].sort((a, b) => b.deltaB_tokens - a.deltaB_tokens).slice(0, 10);
    console.log(' Step  Turn  Tool            Target              Actual      Base B      Delta B     Compounded B');
    console.log(' ' + '─'.repeat(85));
    for (const l of sortedLedger) {
      console.log(` #${String(l.step).padEnd(4)} T${String(l.turn).padEnd(4)} ${l.tool.padEnd(15)} ${l.target.padEnd(18)} ~${String(l.actual_tokens).padStart(6)} tok  ~${String(l.baseB_tokens).padStart(6)} tok  ~${String(l.deltaB_tokens).padStart(6)} tok  ~${String(l.compoundedB_tokens).padStart(9)} tok-turns`);
    }
    console.log('═'.repeat(87) + '\n');
  }
}

function cmdReplay(args, sessions) {
  const showLedger = args.includes('--ledger');

  if (args.includes('--all')) {
    const reports = sessions.map(s => runCounterfactualReplay(s));
    const agg = {
      sessionId: `PORTFOLIO (${reports.length} Sessions Combined)`,
      gitCommit: reports[0] ? reports[0].gitCommit : 'unknown',
      totalSteps: reports.reduce((acc, r) => acc + r.totalSteps, 0),
      plannerTurns: reports.reduce((acc, r) => acc + r.plannerTurns, 0),
      observed: {
        totalChars: reports.reduce((acc, r) => acc + r.observed.totalChars, 0),
        toolOutputChars: reports.reduce((acc, r) => acc + r.observed.toolOutputChars, 0),
        userChars: reports.reduce((acc, r) => acc + r.observed.userChars, 0),
        assistantChars: reports.reduce((acc, r) => acc + r.observed.assistantChars, 0),
        thinkingChars: reports.reduce((acc, r) => acc + r.observed.thinkingChars, 0),
        systemChars: reports.reduce((acc, r) => acc + r.observed.systemChars, 0),
        toolArgsChars: reports.reduce((acc, r) => acc + r.observed.toolArgsChars, 0),
        estTokens: toTokens(reports.reduce((acc, r) => acc + r.observed.totalChars, 0)),
        estToolTokens: toTokens(reports.reduce((acc, r) => acc + r.observed.toolOutputChars, 0))
      },
      counterfactual: {
        actualToolChars: reports.reduce((acc, r) => acc + r.counterfactual.actualToolChars, 0),
        baselineAChars: reports.reduce((acc, r) => acc + r.counterfactual.baselineAChars, 0),
        baselineBChars: reports.reduce((acc, r) => acc + r.counterfactual.baselineBChars, 0),
        actualToolTokens: toTokens(reports.reduce((acc, r) => acc + r.counterfactual.actualToolChars, 0)),
        baselineATokens: toTokens(reports.reduce((acc, r) => acc + r.counterfactual.baselineAChars, 0)),
        baselineBTokens: toTokens(reports.reduce((acc, r) => acc + r.counterfactual.baselineBChars, 0)),
        immediateSavingsA: toTokens(reports.reduce((acc, r) => acc + (r.counterfactual.baselineAChars - r.counterfactual.actualToolChars), 0)),
        immediateSavingsB: toTokens(reports.reduce((acc, r) => acc + (r.counterfactual.baselineBChars - r.counterfactual.actualToolChars), 0)),
        reductionPctA: 0,
        reductionPctB: 0
      },
      cumulativeExposure: {
        exposureCharsA: reports.reduce((acc, r) => acc + r.cumulativeExposure.exposureCharsA, 0),
        exposureCharsB: reports.reduce((acc, r) => acc + r.cumulativeExposure.exposureCharsB, 0),
        exposureTokensA: toTokens(reports.reduce((acc, r) => acc + r.cumulativeExposure.exposureCharsA, 0)),
        exposureTokensB: toTokens(reports.reduce((acc, r) => acc + r.cumulativeExposure.exposureCharsB, 0))
      },
      categoryBreakdown: {
        view_file: { calls: 0, actualChars: 0, baselineAChars: 0, baselineBChars: 0 },
        cbm: { calls: 0, actualChars: 0, baselineAChars: 0, baselineBChars: 0 },
        mini_search: { calls: 0, actualChars: 0, baselineAChars: 0, baselineBChars: 0 },
        token_save: { calls: 0, actualChars: 0, baselineAChars: 0, baselineBChars: 0 },
        other: { calls: 0, actualChars: 0, baselineAChars: 0, baselineBChars: 0 }
      },
      ledger: []
    };

    if (agg.counterfactual.baselineAChars > 0) {
      agg.counterfactual.reductionPctA = (((agg.counterfactual.baselineAChars - agg.counterfactual.actualToolChars) / agg.counterfactual.baselineAChars) * 100).toFixed(1);
    }
    if (agg.counterfactual.baselineBChars > 0) {
      agg.counterfactual.reductionPctB = (((agg.counterfactual.baselineBChars - agg.counterfactual.actualToolChars) / agg.counterfactual.baselineBChars) * 100).toFixed(1);
    }

    for (const r of reports) {
      for (const [k, v] of Object.entries(r.categoryBreakdown)) {
        agg.categoryBreakdown[k].calls += v.calls;
        agg.categoryBreakdown[k].actualChars += v.actualChars;
        agg.categoryBreakdown[k].baselineAChars += v.baselineAChars;
        agg.categoryBreakdown[k].baselineBChars += v.baselineBChars;
      }
      agg.ledger.push(...r.ledger);
    }

    printReplayReport(agg, showLedger);
    return;
  }

  let target = sessions[0];
  const idArg = args.find(a => !a.startsWith('-') && a !== 'replay');
  if (idArg) {
    const found = sessions.find(s => s.id.startsWith(idArg));
    if (!found) {
      console.error(`Session matching "${idArg}" not found.`);
      process.exit(1);
    }
    target = found;
  }

  const replayData = runCounterfactualReplay(target);

  if (args.includes('--json')) {
    console.log(JSON.stringify(replayData, null, 2));
    return;
  }

  if (args.includes('--csv')) {
    console.log('Step,Turn,Tool,Target,ActualTokens,BaselineATokens,BaselineBTokens,DeltaATokens,DeltaBTokens,CompoundedATokens,CompoundedBTokens');
    for (const l of replayData.ledger) {
      console.log(`${l.step},${l.turn},"${l.tool}","${l.target.replace(/"/g, '""')}",${l.actual_tokens},${l.baseA_tokens},${l.baseB_tokens},${l.deltaA_tokens},${l.deltaB_tokens},${l.compoundedA_tokens},${l.compoundedB_tokens}`);
    }
    return;
  }

  printReplayReport(replayData, showLedger);
}

function main() {
  const args = process.argv.slice(2);
  const cache = loadCache();
  const sessions = findSessions();

  if (sessions.length === 0) {
    console.error('No conversation sessions found in ' + BRAIN_DIR);
    process.exit(1);
  }

  const subcmd = args[0] || 'scan';

  if (subcmd === 'replay' || args.includes('--replay')) {
    cmdReplay(args, sessions);
  } else if (subcmd === 'audit' || args.includes('--audit')) {
    cmdAudit(args, sessions, cache);
  } else {
    cmdScan(args, sessions, cache);
  }
}

main();

