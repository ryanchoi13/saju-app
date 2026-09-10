// Bundle only the josa API into the existing single-file deployment.
const fs = require('node:fs');
const path = require('node:path');
const {buildSync} = require('esbuild');
const root = path.join(__dirname, '..');
const result = buildSync({stdin:{contents:'export {josa} from "es-hangul";',resolveDir:root},bundle:true,write:false,format:'iife',globalName:'DalhaHangul',minify:true});
const file = path.join(root,'index.html');
let html = fs.readFileSync(file,'utf8');
const script = '<script id="dalha-hangul">\n/* es-hangul 2.4.0 | MIT | Copyright (c) Viva Republica, Inc. | third_party/es-hangul-LICENSE */\n' + result.outputFiles[0].text + '</script>';
html = html.includes('<script id="dalha-hangul">') ? html.replace(/<script id="dalha-hangul">[\s\S]*?<\/script>/,()=>script) : html.replace('</head>',()=>script+'\n</head>');
fs.writeFileSync(file,html);
fs.mkdirSync(path.join(root,'third_party'),{recursive:true});
fs.copyFileSync(path.join(root,'node_modules/es-hangul/LICENSE'),path.join(root,'third_party/es-hangul-LICENSE'));
