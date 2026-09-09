// Generate language-distribution.svg from GitHub API (35 repos) — manual tool, NOT run by Actions.
// Run: node --use-system-ca scripts/gen_lang_dist.js
const fs = require('fs');
const path = require('path');

const USERNAME = 'dboycht';
const MAX_BAR_W = 290;
const BAR_H = 14;
const ROW_H = 18;
const MARGIN_X = 20;
const MARGIN_Y = 44;
const SVG_W = 480;

const LANG_COLORS = {
  'Python': '#3572A5', 'TypeScript': '#3178c6', 'JavaScript': '#f1e05a',
  'Rust': '#dea584', 'C#': '#178600', 'HTML': '#e34c26', 'CSS': '#563d7c',
  'PowerShell': '#012456', 'Jupyter Notebook': '#DA5B0B', 'Vue': '#4FC08D',
};

// Language label shown in the chart (short name)
function shortLabel(lang) {
  if (!lang) return 'Other';
  if (lang === 'Jupyter Notebook') return 'Jupyter';
  return lang;
}
function colorOf(lang) {
  if (!lang) return '#8b949e'; // Other / null
  return LANG_COLORS[lang] || '#8b949e';
}

async function main() {
  const repos = await fetch(`https://api.github.com/users/${USERNAME}/repos?per_page=100`, {
    headers: { 'User-Agent': 'dsh-writer' },
  }).then(r => r.json());
  if (!Array.isArray(repos)) { console.error('API ERR', JSON.stringify(repos)); process.exit(1); }

  // Count languages across all public repos (null counts as Other)
  const counts = {};
  for (const r of repos) {
    const key = r.language || 'Other';
    counts[key] = (counts[key] || 0) + 1;
  }
  const total = repos.length;

  // Default label for null languages is "Other"; merge anything else that's rare into Other only if user wants.
  const entries = Object.entries(counts).sort((a, b) => b[1] - a[1] || a[0].localeCompare(b[0]));
  const maxCount = Math.max(...entries.map(e => e[1]), 1);

  const rows = entries.map(([lang, count], i) => {
    const y = i * ROW_H;
    const w = Math.max(Math.round(count / maxCount * MAX_BAR_W), 6);
    const label = shortLabel(lang);
    const color = colorOf(lang);
    return `    <!-- ${label} ${count}/${total} = ${(count/total*100).toFixed(1)}% -->\n` +
      `    <text x="0" y="${y + 12}" class="label">${label}</text>\n` +
      `    <rect x="110" y="${y + 1}" width="${w}" height="${BAR_H}" rx="3" fill="${color}"/>\n` +
      `    <text x="${110 + w + 6}" y="${y + 12}" class="count">${count}</text>`;
  }).join('\n');

  const svgH = MARGIN_Y + entries.length * ROW_H + 4;

  const svg = `<svg xmlns="http://www.w3.org/2000/svg" width="${SVG_W}" height="${svgH}" viewBox="0 0 ${SVG_W} ${svgH}">
  <style>
    text { font-family: -apple-system, BlinkMacSystemFont, Segoe UI, Helvetica, Arial, sans-serif; fill: #c9d1d9; }
    .title { font-size: 14px; font-weight: 600; fill: #f0f6fc; }
    .label { font-size: 11px; }
    .count { font-size: 11px; fill: #8b949e; }
  </style>
  <rect width="${SVG_W}" height="${svgH}" rx="8" fill="#0d1117"/>
  <text x="${MARGIN_X}" y="28" class="title">Language Distribution (${total} repos)</text>

  <!-- Bar chart -->
  <g transform="translate(${MARGIN_X}, ${MARGIN_Y})">
${rows}
  </g>
</svg>`;

  const out = path.join(__dirname, '..', 'charts', 'language-distribution.svg');
  fs.writeFileSync(out, svg);
  console.log(`Wrote ${out} (${total} repos)`);
  console.log(entries.map(e => `  ${shortLabel(e[0])}: ${e[1]}`).join('\n'));
}
main().catch(e => { console.error('ERR', e); process.exit(1); });
