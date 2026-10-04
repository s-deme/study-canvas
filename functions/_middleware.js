import cloudflareAccess from '@cloudflare/pages-plugin-cloudflare-access';

export async function onRequest(context) {
  const {env, request} = context;
  // Fail closed on every route, including static files and preview URLs.
  if (!env.DB || !env.OWNER_EMAIL || !env.ACCESS_AUD || !/^https:\/\/[a-z0-9-]+\.cloudflareaccess\.com\/?$/i.test(env.ACCESS_DOMAIN || '')) {
    return Response.json({error:'クラウドのログイン・保存設定が未完了です'}, {status:503});
  }
  if (!request.headers.get('Cf-Access-Jwt-Assertion')) {
    return Response.json({error:'ログインが必要です'}, {status:401});
  }
  const verify = cloudflareAccess({domain:env.ACCESS_DOMAIN.replace(/\/$/,''), aud:env.ACCESS_AUD});
  return verify({...context, next:async () => {
    const claims=context.data.cloudflareAccess?.JWT?.payload;
    if (!claims || claims.iss!==env.ACCESS_DOMAIN.replace(/\/$/,'') || !Array.isArray(claims.aud) || !claims.aud.includes(env.ACCESS_AUD) || !Number.isFinite(claims.exp) || claims.exp<=Date.now()/1000 || (claims.nbf!==undefined && (!Number.isFinite(claims.nbf) || claims.nbf>Date.now()/1000))) {
      return Response.json({error:'ログイン情報を確認できません'}, {status:403});
    }
    const email = claims.email;
    if (typeof email !== 'string' || email.toLowerCase() !== env.OWNER_EMAIL.trim().toLowerCase()) {
      return Response.json({error:'このアカウントは利用できません'}, {status:403});
    }
    // JSON writes require the same origin; headers alone never establish identity.
    if (!['GET','HEAD'].includes(request.method) && request.headers.get('Origin') !== new URL(request.url).origin) {
      return Response.json({error:'送信元を確認できません'}, {status:403});
    }
    context.data.owner = email.toLowerCase();
    const response = await context.next();
    const headers = new Headers(response.headers);
    headers.set('Cache-Control','private, no-store');
    headers.set('X-Content-Type-Options','nosniff');
    headers.set('Referrer-Policy','same-origin');
    headers.set('Content-Security-Policy',"default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; img-src 'self' data: https:; connect-src 'self'; object-src 'none'; base-uri 'none'; frame-ancestors 'none'");
    return new Response(response.body, {status:response.status, statusText:response.statusText, headers});
  }});
}
