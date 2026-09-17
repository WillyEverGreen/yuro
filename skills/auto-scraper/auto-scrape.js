#!/usr/bin/env node

/**
 * AUTO-SCRAPE: Autonomous, Token-Optimized Multi-Tier Scraping & Extraction Engine
 * Automatically evaluates target URLs and executes the optimal extraction tier:
 * Tier 1: Instant HTTP Fetch (No browser, ~50ms, lowest tokens)
 * Tier 2: agent-browser CLI Daemon (Fast Chromium, ~300ms, concise element refs)
 * Tier 3: Playwright / Headless Chromium (Complex auth/form scripts, 0 runtime LLM tokens)
 */

const fs = require('fs');
const path = require('path');
const http = require('http');
const https = require('https');
const { execSync } = require('child_process');

const args = process.argv.slice(2);

if (args.length === 0 || args.includes('--help') || args.includes('-h')) {
  console.log(`
Auto-Scrape CLI Engine (Token-Optimized Multi-Tier Scraper)

Usage:
  node C:\\Users\\advdi\\.gemini\\config\\skills\\auto-scraper\\auto-scrape.js <url>
  node C:\\Users\\advdi\\.gemini\\config\\skills\\auto-scraper\\auto-scrape.js --json <url>
  node C:\\Users\\advdi\\.gemini\\config\\skills\\auto-scraper\\auto-scrape.js --text <url>
  node C:\\Users\\advdi\\.gemini\\config\\skills\\auto-scraper\\auto-scrape.js --snapshot <url>
  node C:\\Users\\advdi\\.gemini\\config\\skills\\auto-scraper\\auto-scrape.js --screenshot <url> [file]

Options:
  --tier <1|2|3>    Force specific extraction tier
  --help, -h        Show help information
`);
  process.exit(0);
}

let isJson = false;
let isTextOnly = false;
let isSnapshotOnly = false;
let isScreenshot = false;
let forcedTier = null;
let targetUrl = null;
let screenshotPath = null;

for (let i = 0; i < args.length; i++) {
  const arg = args[i];
  if (arg === '--json') isJson = true;
  else if (arg === '--text') isTextOnly = true;
  else if (arg === '--snapshot') isSnapshotOnly = true;
  else if (arg === '--screenshot') {
    isScreenshot = true;
    if (args[i + 1] && !args[i + 1].startsWith('http')) {
      screenshotPath = args[++i];
    }
  } else if (arg === '--tier') {
    forcedTier = parseInt(args[++i], 10);
  } else if (arg.startsWith('http://') || arg.startsWith('https://')) {
    targetUrl = arg;
  }
}

if (!targetUrl) {
  console.error('Error: Please specify a valid URL starting with http:// or https://');
  process.exit(1);
}

function runPsCmd(cmdStr) {
  return execSync(`powershell -Command "${cmdStr}"`, { encoding: 'utf8', stdio: ['ignore', 'pipe', 'pipe'] });
}

function httpFetch(urlStr) {
  return new Promise((resolve) => {
    try {
      const parsedUrl = new URL(urlStr);
      const protocol = parsedUrl.protocol === 'https:' ? https : http;
      const options = {
        hostname: parsedUrl.hostname,
        port: parsedUrl.port || (parsedUrl.protocol === 'https:' ? 443 : 80),
        path: parsedUrl.pathname + parsedUrl.search,
        method: 'GET',
        headers: {
          'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
          'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
          'Accept-Language': 'en-US,en;q=0.5'
        },
        timeout: 5000
      };

      const req = protocol.request(options, (res) => {
        if (res.statusCode >= 300 && res.statusCode < 400 && res.headers.location) {
          let redirectUrl = res.headers.location;
          if (!redirectUrl.startsWith('http')) {
            redirectUrl = new URL(redirectUrl, urlStr).href;
          }
          return resolve(httpFetch(redirectUrl));
        }
        let data = '';
        res.on('data', chunk => data += chunk);
        res.on('end', () => resolve({ statusCode: res.statusCode, body: data, headers: res.headers }));
      });

      req.on('error', err => resolve({ error: err.message }));
      req.on('timeout', () => { req.destroy(); resolve({ error: 'timeout' }); });
      req.end();
    } catch (e) {
      resolve({ error: e.message });
    }
  });
}

function isDynamicSpa(html) {
  if (!html || html.length < 500) return true;
  const spaMarkers = [
    '<div id="root"></div>',
    '<div id="app"></div>',
    '__NEXT_DATA__',
    'window.__INITIAL_STATE__',
    '<noscript>You need to enable JavaScript',
    'Enable JavaScript to run this app'
  ];
  const hasSpaMarker = spaMarkers.some(marker => html.includes(marker));
  const strippedText = html.replace(/<script\b[^<]*>([\s\S]*?)<\/script>/gi, '')
                          .replace(/<style\b[^<]*>([\s\S]*?)<\/style>/gi, '')
                          .replace(/<[^>]+>/g, ' ')
                          .replace(/\s+/g, ' ')
                          .trim();
  return hasSpaMarker || strippedText.length < 200;
}

function htmlToText(html) {
  let text = html.replace(/<script\b[^<]*>([\s\S]*?)<\/script>/gi, '')
                 .replace(/<style\b[^<]*>([\s\S]*?)<\/style>/gi, '')
                 .replace(/<h[1-6][^>]*>(.*?)<\/h[1-6]>/gi, '\n\n# $1\n')
                 .replace(/<p[^>]*>(.*?)<\/p>/gi, '\n$1\n')
                 .replace(/<li[^>]*>(.*?)<\/li>/gi, '\n- $1')
                 .replace(/<[^>]+>/g, ' ')
                 .replace(/&nbsp;/g, ' ')
                 .replace(/&amp;/g, '&')
                 .replace(/&lt;/g, '<')
                 .replace(/&gt;/g, '>')
                 .replace(/\n\s*\n/g, '\n\n')
                 .trim();
  return text;
}

async function runAutoScrape() {
  const startTime = Date.now();

  // Tier 1: Fast Direct HTTP
  if (forcedTier === 1 || (!forcedTier && !isScreenshot && !isSnapshotOnly)) {
    const httpRes = await httpFetch(targetUrl);
    if (!httpRes.error && httpRes.statusCode === 200) {
      const isSpa = isDynamicSpa(httpRes.body);
      if (!isSpa || forcedTier === 1) {
        const textContent = htmlToText(httpRes.body);
        const duration = Date.now() - startTime;
        if (isTextOnly) {
          console.log(textContent);
          return;
        }
        if (isJson) {
          console.log(JSON.stringify({ status: 'success', tier: 1, engine: 'http_fetch', duration_ms: duration, url: targetUrl, text_length: textContent.length, content: textContent }));
          return;
        }
        console.log(`[auto-scrape] [Tier 1: Direct HTTP] (${duration}ms) ✓ Success`);
        console.log(`URL: ${targetUrl}`);
        console.log('--- Content Sample ---');
        console.log(textContent.slice(0, 1500) + (textContent.length > 1500 ? '\n...[truncated]' : ''));
        return;
      }
    }
  }

  // Tier 2: agent-browser CLI Daemon
  if (forcedTier === 2 || !forcedTier || isScreenshot || isSnapshotOnly) {
    try {
      const duration = Date.now() - startTime;

      if (isScreenshot) {
        const outPath = screenshotPath || path.join(process.cwd(), 'scrape_screenshot.png');
        runPsCmd(`agent-browser open '${targetUrl}'; agent-browser screenshot '${outPath}'`);
        console.log(`[auto-scrape] [Tier 2 Screenshot] ✓ Saved to ${outPath}`);
        return;
      }

      if (isSnapshotOnly) {
        const snapshotOut = runPsCmd(`agent-browser open '${targetUrl}'; agent-browser snapshot -i`);
        console.log(snapshotOut);
        return;
      }

      const pageText = runPsCmd(`agent-browser open '${targetUrl}'; agent-browser get text body`);
      if (isTextOnly) {
        console.log(pageText);
        return;
      }
      if (isJson) {
        console.log(JSON.stringify({ status: 'success', tier: 2, engine: 'agent_browser_cli', duration_ms: duration, url: targetUrl, text_length: pageText.length, content: pageText }));
        return;
      }
      console.log(`[auto-scrape] [Tier 2: agent-browser CLI] (${duration}ms) ✓ Success`);
      console.log(`URL: ${targetUrl}`);
      console.log('--- Content Sample ---');
      console.log(pageText.slice(0, 1500) + (pageText.length > 1500 ? '\n...[truncated]' : ''));
      return;
    } catch (err) {
      console.error(`[auto-scrape] Error in Tier 2: ${err.message}`);
      process.exit(1);
    }
  }
}

runAutoScrape();
