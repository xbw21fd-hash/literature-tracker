/**
 * Bookmark exporters: RSS / Markdown / BibTeX.
 * Each function takes a list of bookmark records and returns a Blob.
 */
(function () {
  'use strict';

  function _escapeXml(s) {
    return String(s == null ? '' : s)
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;')
      .replace(/'/g, '&#39;');
  }

  function _cdata(s) {
    return '<![CDATA[' + String(s == null ? '' : s).replace(/\]\]>/g, ']]]]><![CDATA[>') + ']]>';
  }

  function _rfc822(date) {
    if (!date) return '';
    const d = new Date(date + 'T00:00:00+0800');
    if (isNaN(d.getTime())) return '';
    return d.toUTCString();
  }

  function _shortHash(s) {
    let h = 0;
    for (let i = 0; i < s.length; i++) h = ((h << 5) - h + s.charCodeAt(i)) | 0;
    return ('00000000' + (h >>> 0).toString(36)).slice(-8);
  }

  function _arxivIdFromUrl(url) {
    const m = String(url || '').match(/arxiv\.org\/abs\/([^?#\s]+)/i);
    return m ? m[1].replace(/\/+$/, '') : null;
  }

  function exportRSS(list) {
    const today = new Date().toISOString().slice(0, 10);
    const items = list.map(it => {
      const title = [it.title_zh, it.title_en].filter(Boolean).join(' / ') || it.link;
      const desc = [it.abstract_zh, it.summary].filter(Boolean).join('\n\n');
      const pub = _rfc822(it.source_date);
      return `    <item>
      <title>${_cdata(title)}</title>
      <link>${_escapeXml(it.link)}</link>
      <description>${_cdata(desc)}</description>
      ${pub ? `<pubDate>${pub}</pubDate>` : ''}
      ${it.journal ? `<source>${_escapeXml(it.journal)}</source>` : ''}
      <guid isPermaLink="true">${_escapeXml(it.link)}</guid>
    </item>`;
    }).join('\n');

    const xml = `<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0">
  <channel>
    <title>我的文献收藏 · ${today}</title>
    <link>https://hongyu-yu.github.io/literature-tracker/</link>
    <description>从 literature-tracker 导出的 ${list.length} 篇收藏</description>
    <generator>literature-tracker bookmarks export</generator>
    <pubDate>${new Date().toUTCString()}</pubDate>
${items}
  </channel>
</rss>
`;
    return new Blob([xml], { type: 'application/rss+xml;charset=utf-8' });
  }

  function exportMarkdown(list) {
    const today = new Date().toISOString().slice(0, 10);
    const lines = [`# 我的文献收藏 · ${today}（共 ${list.length} 篇）`, ''];
    for (const it of list) {
      const ttl = it.title_zh || it.title_en || it.link;
      lines.push(`## ${ttl}`);
      if (it.title_en && it.title_en !== it.title_zh) lines.push(`**EN**：${it.title_en}`);
      const meta = [it.journal && `**期刊**：${it.journal}`, it.source_date && `收录日期：${it.source_date}`].filter(Boolean).join('  ·  ');
      if (meta) lines.push(meta);
      if (it.abstract_zh) lines.push(`**摘要**：${it.abstract_zh}`);
      if (it.summary) lines.push(`**亮点**：${it.summary}`);
      lines.push(`[原文 ↗](${it.link})`);
      lines.push('');
      lines.push('---');
      lines.push('');
    }
    return new Blob([lines.join('\n')], { type: 'text/markdown;charset=utf-8' });
  }

  function exportBibTeX(list) {
    const entries = list.map(it => {
      const arxivId = _arxivIdFromUrl(it.link);
      const year = (it.source_date || '').slice(0, 4) || '';
      const titleField = it.title_en || it.title_zh || it.link;
      const author = (it.authors && it.authors.length) ? it.authors.join(' and ') : 'Unknown';
      if (arxivId) {
        return `@misc{arxiv:${arxivId},
  title={${titleField}},
  author={${author}},
  year={${year}},
  eprint={${arxivId}},
  archivePrefix={arXiv},
  url={${it.link}}
}`;
      } else {
        const key = _shortHash(it.link);
        return `@misc{${key},
  title={${titleField}},
  author={${author}},
  year={${year}},
  howpublished={\\url{${it.link}}},
  note={${it.journal || ''}}
}`;
      }
    }).join('\n\n');
    return new Blob([entries + '\n'], { type: 'application/x-bibtex;charset=utf-8' });
  }

  window.BookmarkExports = { exportRSS, exportMarkdown, exportBibTeX };
})();
