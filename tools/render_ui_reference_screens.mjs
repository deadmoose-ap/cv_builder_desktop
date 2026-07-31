/* Render deterministic Calm Workspace reference images for UI review. */
import { createRequire } from 'node:module';
import { mkdir } from 'node:fs/promises';
import { resolve } from 'node:path';

const require = createRequire(import.meta.url);
const { chromium } = require('playwright');
const output = resolve(import.meta.dirname, '..', 'ui-reference');
await mkdir(output, { recursive: true });

const css = `
  * { box-sizing: border-box; }
  body { margin:0; color:#172033; background:#f6f7fb; font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif; }
  .window { width:1440px; height:960px; overflow:hidden; display:flex; flex-direction:column; background:#f6f7fb; }
  .titlebar { height:64px; flex:none; display:flex; align-items:center; gap:11px; padding:0 18px; background:#fff; border-bottom:1px solid #d7dde8; }
  .traffic { display:flex; gap:8px; margin-right:8px; } .dot { width:13px; height:13px; border-radius:50%; }
  .red{background:#ff5f57}.yellow{background:#febc2e}.green{background:#28c840}
  .brand { font-size:17px; font-weight:700; } .file-status { margin-left:16px; color:#667085; font-size:13px; }
  .toolbar { margin-left:auto; display:flex; align-items:center; gap:7px; }
  button { appearance:none; border:0; border-radius:8px; padding:10px 15px; color:#172033; background:transparent; font:inherit; font-size:13px; }
  button.secondary { background:#fff; border:1px solid #d7dde8; } button.primary { color:#fff; background:#2f6bff; font-weight:650; }
  .workspace { min-height:0; flex:1; display:grid; grid-template-columns:218px 1fr; }
  .sidebar { padding:27px 14px; background:#eff3f8; display:flex; flex-direction:column; }
  .eyebrow { color:#667085; font-size:11px; font-weight:700; letter-spacing:.08em; text-transform:uppercase; }
  .completion { margin:10px 8px 8px; font-size:14px; } .progress { height:6px; margin:0 8px; overflow:hidden; border-radius:9px; background:#d7dde8; }
  .progress i { display:block; width:100%; height:100%; background:#2f6bff; }
  .nav { display:grid; gap:5px; margin-top:26px; } .nav-item { padding:13px 14px; border-radius:9px; color:#667085; font-size:14px; }
  .nav-item.active { color:#2f6bff; background:#eaf0ff; font-weight:650; }
  .nav-item span { display:inline-block; width:26px; }
  .private { margin:auto 8px 0; color:#667085; font-size:12px; line-height:1.55; }
  main { min-width:0; overflow:hidden; padding:35px 44px 40px; }
  .screen-head { max-width:970px; display:flex; align-items:flex-end; justify-content:space-between; gap:20px; margin-bottom:23px; }
  h1 { margin:5px 0 6px; font-size:28px; letter-spacing:-.02em; } h2 { margin:0; font-size:16px; } p { margin:0; }
  .subtle { color:#667085; font-size:14px; } .card { max-width:970px; padding:24px; background:#fff; border:1px solid #d7dde8; border-radius:13px; }
  .form-grid { display:grid; grid-template-columns:1fr 1fr; gap:16px 18px; } .field.full { grid-column:1/-1; }
  label { display:block; margin:0 0 7px; font-size:13px; font-weight:650; }
  .label-row { display:flex; justify-content:space-between; } .hint { color:#667085; font-size:12px; font-weight:400; }
  input, textarea { width:100%; border:1px solid #d7dde8; border-radius:8px; padding:11px 12px; color:#172033; background:#fff; font:inherit; font-size:14px; outline:none; }
  input::placeholder, textarea::placeholder { color:#667085; opacity:1; }
  textarea { resize:none; line-height:1.5; } .skills { height:128px; } .summary { height:590px; }
  .count { margin-top:9px; text-align:right; color:#667085; font-size:12px; }
  .entry-list { max-width:970px; display:grid; gap:11px; }
  .entry { padding:18px; background:#fff; border:1px solid #d7dde8; border-radius:12px; display:flex; align-items:center; }
  .entry h2 { margin-bottom:5px; } .meta { margin-top:6px; color:#667085; font-size:13px; }
  .entry-actions { margin-left:auto; display:flex; align-items:center; gap:5px; }
  .danger { color:#b42318; }
  .editor-card { max-width:970px; padding:22px 24px; background:#fff; border:1px solid #d7dde8; border-radius:13px; }
  .editor-grid { display:grid; grid-template-columns:1fr 1fr; gap:14px 18px; } .editor-grid .full { grid-column:1/-1; }
  .editor-grid textarea { height:78px; } .editor-grid textarea.medium { height:92px; }
  .editor-actions { max-width:970px; display:flex; justify-content:flex-end; gap:8px; margin-top:15px; }
  .library { padding:36px 44px; } .library h1 { margin:6px 0 24px; }
  .library-card { padding:20px; display:flex; align-items:center; max-width:none; }
`;

const navigation = (active) => ['Profile', 'Summary', 'Experience', 'Education']
  .map((name, index) => `<div class="nav-item ${name.toLowerCase() === active ? 'active' : ''}"><span>${index + 1}</span>${name}</div>`)
  .join('');

function shell(active, content) {
  return `<html><head><style>${css}</style></head><body><div class="window">
    <header class="titlebar"><div class="traffic"><i class="dot red"></i><i class="dot yellow"></i><i class="dot green"></i></div><div class="brand">CV Builder</div><div class="file-status">Product Designer CV · Saved</div>
      <div class="toolbar"><button>All CVs</button><button class="secondary">Export JSON</button><button class="primary">Export PDF</button></div>
    </header>
    <div class="workspace"><aside class="sidebar"><div class="eyebrow" style="margin-left:8px">Build your CV</div><div class="completion">0% complete</div><div class="progress"><i style="width:0"></i></div><nav class="nav">${navigation(active)}</nav><div class="private">Local and private<br>Your data stays on this device.</div></aside>${content}</div>
  </div></body></html>`;
}

const head = (step, title, subtitle, action = '') => `<div class="screen-head"><div><div class="eyebrow">${step}</div><h1>${title}</h1><p class="subtle">${subtitle}</p></div>${action}</div>`;

const profile = shell('profile', `<main>${head('Section 1 of 4','Profile','The essential details shown at the top of your CV.')}
  <section class="card"><div class="form-grid">
    <div class="field full"><label>Full name</label><input placeholder="YOUR NAME"></div>
    <div class="field full"><label>Professional headline</label><input placeholder="YOUR JOB TITLE | YOUR SPECIALIZATION | YOUR KEY VALUE"></div>
    <div class="field"><label>Location</label><input placeholder="YOUR CITY, YOUR COUNTRY"></div>
    <div class="field"><label>Email</label><input placeholder="your.email@example.com"></div>
    <div class="field full"><label>LinkedIn or website</label><input placeholder="linkedin.com/in/your-profile"></div>
    <div class="field full"><div class="label-row"><label>Core skills</label><span class="hint">One skill per line</span></div><textarea class="skills" placeholder="SKILL ONE&#10;SKILL TWO&#10;SKILL THREE"></textarea></div>
  </div></section></main>`);

const summaryText = `Write a short introduction about your professional background and main expertise.

Describe the teams, projects, or products you have worked with.

Highlight your most relevant results and areas of specialization.`;
const summary = shell('summary', `<main>${head('Section 2 of 4','Summary','Use a blank line between paragraphs.')}
  <section class="card"><label>Professional summary</label><textarea class="summary" placeholder="${summaryText}"></textarea><div class="count">0 characters</div></section></main>`);

const experience = shell('experience', `<main>${head('Section 3 of 4','Experience','Put the most relevant role first.','<button class="primary">＋ Add role</button>')}
  <section class="card" style="text-align:center"><h2>No experience added yet</h2><p class="subtle" style="margin:7px 0 16px">Add a role to show your responsibilities and impact.</p><button class="primary">＋ Add your first role</button></section></main>`);

const education = shell('education', `<main>${head('Section 4 of 4','Education','Add the qualification most relevant to this CV.')}
  <section class="card"><div class="form-grid">
    <div class="field full"><label>Institution</label><input placeholder="UNIVERSITY OR SCHOOL NAME"></div>
    <div class="field full"><label>Qualification and dates</label><input placeholder="DEGREE OR QUALIFICATION (YEAR – YEAR)"></div>
  </div></section></main>`);

const editor = shell('experience', `<main>${head('Section 3 of 4','Add experience','Describe the role, responsibilities and measurable results.')}
  <section class="editor-card"><div class="editor-grid">
    <div class="field full"><label>Company</label><input placeholder="CURRENT OR MOST RECENT COMPANY"></div>
    <div class="field full"><label>Role</label><input placeholder="YOUR JOB TITLE"></div>
    <div class="field"><label>Dates</label><input placeholder="MONTH YEAR – PRESENT"></div>
    <div class="field"><label>Total duration</label><input placeholder="X YEARS X MONTHS"></div>
    <div class="field full"><label>Location</label><input placeholder="CITY, COUNTRY"></div>
    <div class="field full"><label>Role or project description</label><textarea placeholder="Add a one-sentence role or project description."></textarea></div>
    <div class="field full"><div class="label-row"><label>Key responsibilities</label><span class="hint">One item per line</span></div><textarea class="medium" placeholder="Describe a key responsibility.&#10;Describe another contribution."></textarea></div>
    <div class="field full"><div class="label-row"><label>Results</label><span class="hint">One item per line</span></div><textarea placeholder="Describe a measurable result or business impact."></textarea></div>
  </div></section><div class="editor-actions"><button class="secondary">Cancel</button><button class="primary">Save entry</button></div></main>`);

const library = `<html><head><style>${css}</style></head><body><div class="window">
  <header class="titlebar"><div class="traffic"><i class="dot red"></i><i class="dot yellow"></i><i class="dot green"></i></div><div class="brand">CV Builder</div><div class="file-status">Your CV library</div>
    <div class="toolbar"><button>Example JSON</button><button class="secondary">Import JSON</button><button class="primary">＋ New CV</button></div></header>
  <main class="library"><div class="eyebrow">Your documents</div><h1>Choose a CV to continue</h1>
    <section class="card library-card"><div><h2>Product Designer CV</h2><p class="subtle" style="margin-top:7px">No name added yet · 0% complete</p><p class="subtle" style="margin-top:7px">Updated recently</p></div>
      <div class="entry-actions"><button class="secondary">Open</button><button>Rename</button><button class="danger">Delete</button></div></section>
  </main></div></body></html>`;

const browser = await chromium.launch({
  headless: true,
  executablePath: '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',
});
const page = await browser.newPage({ viewport: { width: 1440, height: 960 }, deviceScaleFactor: 1 });
for (const [name, html] of [
  ['00-library', library],
  ['01-profile', profile],
  ['02-summary', summary],
  ['03-experience', experience],
  ['04-education', education],
  ['05-experience-editor', editor],
]) {
  await page.setContent(html);
  await page.waitForTimeout(80);
  await page.screenshot({ path: resolve(output, `${name}.png`) });
  await page.pdf({
    path: resolve(output, `${name}.pdf`),
    width: '1440px',
    height: '960px',
    printBackground: true,
    margin: { top: '0', right: '0', bottom: '0', left: '0' },
  });
}
await browser.close();
