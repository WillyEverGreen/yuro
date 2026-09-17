/**
 * E2E TEST SUITE FOR AUTO-SCRAPER ENGINE
 * Systematically tests every tier, flag, and output format.
 */

const { execSync } = require('child_process');
const fs = require('fs');
const path = require('path');

const scriptPath = path.join(__dirname, 'auto-scrape.js');
let passed = 0;
let failed = 0;

function runTest(testName, cmd) {
  console.log(`\n========================================`);
  console.log(`RUNNING TEST: ${testName}`);
  console.log(`Command: ${cmd}`);
  console.log(`========================================`);
  const start = Date.now();
  try {
    const output = execSync(cmd, { encoding: 'utf8', stdio: ['ignore', 'pipe', 'pipe'] });
    const duration = Date.now() - start;
    console.log(`STATUS: ✓ PASS (${duration}ms)`);
    console.log(`OUTPUT SAMPLE:\n${output.slice(0, 300)}...`);
    passed++;
    return output;
  } catch (err) {
    const duration = Date.now() - start;
    console.error(`STATUS: ❌ FAIL (${duration}ms)`);
    console.error(`ERROR: ${err.message}`);
    failed++;
    return null;
  }
}

async function main() {
  console.log('🚀 STARTING AUTO-SCRAPER E2E SUITE');

  // Test Case 1: Tier 1 Static Extraction
  runTest(
    'Test 1: Tier 1 Direct HTTP Extraction (example.com)',
    `node "${scriptPath}" https://example.com`
  );

  // Test Case 2: JSON Output Format
  const jsonOut = runTest(
    'Test 2: Tier 1 JSON Output (--json)',
    `node "${scriptPath}" --json https://example.com`
  );
  if (jsonOut) {
    try {
      const parsed = JSON.parse(jsonOut);
      if (parsed.status === 'success' && parsed.tier === 1) {
        console.log('-> JSON structure validated successfully!');
      }
    } catch (e) {
      console.error('-> JSON validation failed!');
    }
  }

  // Test Case 3: Plain Text Only
  runTest(
    'Test 3: Plain Text Output (--text)',
    `node "${scriptPath}" --text https://example.com`
  );

  // Test Case 4: Tier 2 Interactive Snapshot
  runTest(
    'Test 4: Tier 2 Accessibility Snapshot (--snapshot)',
    `node "${scriptPath}" --snapshot https://html.duckduckgo.com/html/`
  );

  // Test Case 5: Dynamic Site Tier 2 Extraction
  runTest(
    'Test 5: Tier 2 Dynamic Site Extraction (Hacker News)',
    `node "${scriptPath}" --tier 2 https://news.ycombinator.com`
  );

  // Test Case 6: Screenshot Generation
  const shotPath = path.join(__dirname, 'e2e_test_screenshot.png');
  runTest(
    'Test 6: Page Screenshot Export (--screenshot)',
    `node "${scriptPath}" --screenshot https://example.com "${shotPath}"`
  );
  if (fs.existsSync(shotPath)) {
    console.log(`-> Screenshot file verified at: ${shotPath}`);
  }

  console.log(`\n========================================`);
  console.log(`E2E TEST RESULTS: ${passed} PASSED, ${failed} FAILED`);
  console.log(`========================================\n`);

  if (failed > 0) process.exit(1);
}

main();
