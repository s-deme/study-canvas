// Pages uses its standard config redirect instead of the unsupported --config flag.
import {accessSync,mkdirSync,writeFileSync} from 'node:fs';

// Check first: never fall back to the public template when local config is missing.
accessSync('wrangler.local.jsonc');
mkdirSync('.wrangler/deploy',{recursive:true});
writeFileSync('.wrangler/deploy/config.json',JSON.stringify({configPath:'../../wrangler.local.jsonc'})+'\n');
