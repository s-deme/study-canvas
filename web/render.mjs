// Deliberately small Markdown subset: escaped text, tables, code, paragraphs.
// Imported HTML is never interpreted. Images are rendered only after validation.
export const esc=value=>String(value).replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
export const inlineText=value=>esc(value).replace(/［(上付き|下付き|太字・斜体|太字|斜体|下線|上線)：([^［］]+)］/g,(_,kind,text)=>{
  if(kind==='上線') return `<span style="text-decoration:overline" aria-label="${text}の否定">${text}</span>`;
  if(kind==='太字・斜体') return `<strong><i>${text}</i></strong>`;
  const tag={上付き:'sup',下付き:'sub',太字:'strong',斜体:'i',下線:'u'}[kind];return `<${tag}>${text}</${tag}>`;
});
export function richText(value) {
  const lines=String(value).split(/\r?\n/);let html='';
  for(let i=0;i<lines.length;i++) {
    if(lines[i].startsWith('```')) {const code=[];while(++i<lines.length && !lines[i].startsWith('```')) code.push(lines[i]);html+=`<pre tabindex="0" aria-label="コード（横にスクロールできます）"><code>${esc(code.join('\n'))}</code></pre>`;}
    else if(lines[i].trim().startsWith('|') && /^\s*\|?\s*:?-{3,}/.test(lines[i+1] || '')) {
      const cells=line=>line.trim().replace(/^\||\|$/g,'').split('|').map(c=>c.trim());
      const heads=cells(lines[i]);i++;const rows=[];while(i+1<lines.length && lines[i+1].trim().startsWith('|')) rows.push(cells(lines[++i]));
      html+='<div class="table-scroll" tabindex="0" role="region" aria-label="表（横にスクロールできます）"><table><thead><tr>'+heads.map(c=>`<th scope="col">${inlineText(c)}</th>`).join('')+'</tr></thead><tbody>'+rows.map(r=>'<tr>'+r.map(c=>`<td>${inlineText(c)}</td>`).join('')+'</tr>').join('')+'</tbody></table></div>';
    }else if(lines[i].trim()) {const block=[lines[i]];while(i+1<lines.length && lines[i+1].trim() && !lines[i+1].startsWith('```') && !(lines[i+1].trim().startsWith('|') && /^\s*\|?\s*:?-{3,}/.test(lines[i+2] || ''))) block.push(lines[++i]);html+=`<p class="explanation">${inlineText(block.join('\n'))}</p>`;}
  }return html;
}
