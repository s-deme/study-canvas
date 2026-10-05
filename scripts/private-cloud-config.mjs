import {readFileSync,writeFileSync,mkdirSync} from 'node:fs';
// Existing personal credentials/bindings remain local. Only the output directory changes.
const raw=readFileSync('wrangler.local.jsonc','utf8');
if(!/"pages_build_output_dir"\s*:\s*"[^"]+"/.test(raw)) throw new Error('Missing pages_build_output_dir');
mkdirSync('build/private/.wrangler/deploy',{recursive:true});
writeFileSync('build/private/wrangler.jsonc',raw.replace(/"pages_build_output_dir"\s*:\s*"[^"]+"/,'"pages_build_output_dir": "./web"'));
writeFileSync('build/private/.wrangler/deploy/config.json',JSON.stringify({configPath:'../../wrangler.jsonc'}));
console.log('Private Pages configuration prepared; values not printed');
