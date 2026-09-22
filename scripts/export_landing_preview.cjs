// Build a portable, non-authenticating approval artifact from the actual landing.
const fs = require('node:fs'), path = require('node:path');
const root = path.join(__dirname, '..');
const {JSDOM} = require('jsdom');
const dom = new JSDOM(fs.readFileSync(path.join(root, 'index.html'), 'utf8'));
const doc = dom.window.document;
const header = doc.querySelector('.app-container > header').cloneNode(true);
header.querySelector('#headerAuthArea').remove();
header.querySelectorAll('[onclick]').forEach(n => n.removeAttribute('onclick'));
const gate = doc.getElementById('view-login-gate').cloneNode(true);
gate.querySelectorAll('[onclick]').forEach(n => n.removeAttribute('onclick'));
const styles = [...doc.querySelectorAll('style')].map(n => n.textContent).join('\n') +
    '\n' + fs.readFileSync(path.join(root, 'assets/design-system.css'), 'utf8') +
    '\n' + fs.readFileSync(path.join(root, 'assets/landing.css'), 'utf8');
const output = process.argv[2];
if (!output) throw Error('Provide the output HTML path');
fs.writeFileSync(output, `<!doctype html><html lang="ko" data-design="clear"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><title>달하 랜딩 · 승인 전 시안</title><style>${styles}</style></head><body><div class="app-container">${header.outerHTML}<main>${gate.outerHTML}</main><p id="preview-status" role="status" style="padding:16px;text-align:center;font-size:12px;color:#435748">승인 전 시안 · 실제 로그인 및 개인정보 저장은 하지 않습니다.</p></div><script>document.getElementById('btnKakaoLogin').addEventListener('click',()=>{const n=document.getElementById('preview-status');n.textContent='시안 확인용 버튼입니다. 운영 반영 후 카카오 로그인으로 연결됩니다.';n.scrollIntoView({block:'center'});});</script></body></html>`, 'utf8');
dom.window.close();
console.log('Exported approval-only landing preview');
