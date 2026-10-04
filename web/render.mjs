// Deliberately small Markdown subset: escaped text, tables, code, paragraphs.
// Imported HTML is never interpreted. Images are rendered only after validation.
export const esc=value=>String(value).replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
export function richText(value) {
  const lines=String(value).split(/\r?\n/);let html='';
  for(let i=0;i<lines.length;i++) {
    if(lines[i].startsWith('```')) {const code=[];while(++i<lines.length && !lines[i].startsWith('```')) code.push(lines[i]);html+=`<pre><code>${esc(code.join('\n'))}</code></pre>`;}
    else if(lines[i].trim().startsWith('|') && /^\s*\|?\s*:?-{3,}/.test(lines[i+1] || '')) {
      const cells=line=>line.trim().replace(/^\||\|$/g,'').split('|').map(c=>c.trim());
      const heads=cells(lines[i]);i++;const rows=[];while(i+1<lines.length && lines[i+1].trim().startsWith('|')) rows.push(cells(lines[++i]));
      html+='<div class="table-scroll"><table><thead><tr>'+heads.map(c=>`<th scope="col">${esc(c)}</th>`).join('')+'</tr></thead><tbody>'+rows.map(r=>'<tr>'+r.map(c=>`<td>${esc(c)}</td>`).join('')+'</tr>').join('')+'</tbody></table></div>';
    }else if(lines[i].trim()) {const block=[lines[i]];while(i+1<lines.length && lines[i+1].trim() && !lines[i+1].startsWith('```') && !(lines[i+1].trim().startsWith('|') && /^\s*\|?\s*:?-{3,}/.test(lines[i+2] || ''))) block.push(lines[++i]);html+=`<p class="explanation">${esc(block.join('\n'))}</p>`;}
  }return html;
}
