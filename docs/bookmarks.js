/**
 * Bookmarks for literature-tracker (mobile-friendly star + export).
 * Storage: localStorage key "literature_bookmarks", value = { [link]: meta }.
 */
(function () {
  'use strict';
  const STORAGE_KEY = 'literature_bookmarks';
  const LEGACY_KEY = 'literature_favorites';

  function _isLikelyUrl(s) {
    return typeof s === 'string' && /^https?:\/\//i.test(s);
  }

  class BookmarkStore {
    constructor() {
      this.data = this._load();
      this._migrateLegacy();
    }

    _load() {
      try {
        const raw = localStorage.getItem(STORAGE_KEY);
        return raw ? JSON.parse(raw) : {};
      } catch (e) {
        console.warn('[bookmarks] failed to load:', e);
        return {};
      }
    }

    _save() {
      try {
        localStorage.setItem(STORAGE_KEY, JSON.stringify(this.data));
      } catch (e) {
        console.warn('[bookmarks] failed to save:', e);
      }
    }

    _migrateLegacy() {
      try {
        const raw = localStorage.getItem(LEGACY_KEY);
        if (!raw) return;
        const arr = JSON.parse(raw);
        if (!Array.isArray(arr)) {
          localStorage.removeItem(LEGACY_KEY);
          return;
        }
        let migrated = 0;
        for (const id of arr) {
          if (_isLikelyUrl(id) && !this.has(id)) {
            this.data[id] = {
              title_zh: '',
              title_en: '',
              journal: '',
              source_type: 'legacy',
              source_date: '',
              added_at: Date.now(),
            };
            migrated++;
          }
        }
        if (migrated > 0) this._save();
        localStorage.removeItem(LEGACY_KEY);
      } catch (e) {
        console.warn('[bookmarks] legacy migration failed:', e);
      }
    }

    has(link) { return Object.prototype.hasOwnProperty.call(this.data, link); }
    count() { return Object.keys(this.data).length; }

    add(link, meta) {
      if (!link || this.has(link)) return false;
      this.data[link] = Object.assign({}, meta || {}, { added_at: Date.now() });
      this._save();
      this._fire();
      return true;
    }

    remove(link) {
      if (!this.has(link)) return false;
      delete this.data[link];
      this._save();
      this._fire();
      return true;
    }

    toggle(link, meta) {
      if (this.has(link)) {
        this.remove(link);
        return false;
      }
      this.add(link, meta);
      return true;
    }

    list() {
      return Object.entries(this.data).map(([link, meta]) => Object.assign({ link }, meta));
    }

    _fire() {
      try {
        document.dispatchEvent(new CustomEvent('bookmarkschange', {
          detail: { count: this.count() }
        }));
      } catch {}
    }
  }

  function _escapeHtml(s) {
    return String(s == null ? '' : s)
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;')
      .replace(/'/g, '&#39;');
  }

  function _hostname(url) {
    try { return new URL(url).hostname.replace(/^www\./, ''); } catch { return ''; }
  }

  const CARD_SELECTORS = [
    '.daily-paper-card',
    '.daily-news-item',
    '.daily-core-card',
    '.weekly-core-card',
    '.weekly-paper-card',
    '.feed-card',
  ];

  function _text(node) {
    return node ? node.textContent.replace(/\s+/g, ' ').trim() : '';
  }

  function _extractMeta(card) {
    const titleZhEl =
      card.querySelector('.daily-paper-title-zh, .daily-news-title-zh, .daily-core-title-zh, .weekly-core-title-zh');
    const titleEnEl =
      card.querySelector('.daily-paper-title-en, .daily-news-title-en, .daily-core-title-en, .weekly-core-title-en');
    let title_zh = _text(titleZhEl).replace(/#$/, '').trim();
    let title_en = _text(titleEnEl).replace(/#$/, '').trim();

    let journal = '';
    const chip = card.querySelector('.daily-chip-journal, .weekly-chip-journal, .weekly-chip');
    if (chip) {
      const t = _text(chip).replace(/^📖\s*/, '');
      journal = t.split(/[/·]/)[0].trim();
    }

    let abstract_zh = '';
    const absEl = card.querySelector('.daily-paper-abstract, .weekly-core-abs');
    if (absEl) abstract_zh = _text(absEl).replace(/^📄\s*摘要[:：]\s*/, '');

    let summary = '';
    const sumEl = card.querySelector('.daily-paper-highlight');
    if (sumEl) summary = _text(sumEl).replace(/^💡\s*亮点[:：]\s*/, '');

    let source_type = 'daily';
    if (/weekly-/.test(card.className)) source_type = 'weekly';
    let source_date = '';
    const dateMatch = location.pathname.match(/(\d{4}-\d{2}-\d{2})\.html/);
    if (dateMatch) source_date = dateMatch[1];

    return { title_zh, title_en, journal, abstract_zh, summary, source_type, source_date };
  }

  class BookmarkUI {
    constructor(store) {
      this.store = store;
    }

    attachToCards(root = document) {
      const cards = root.querySelectorAll(CARD_SELECTORS.join(','));
      cards.forEach(card => this._attach(card));
    }

    _attach(card) {
      if (card.querySelector(':scope > .bookmark-btn')) return;
      const link = card.dataset.bookmarkKey;
      if (!link) return;

      const btn = document.createElement('button');
      btn.type = 'button';
      btn.className = 'bookmark-btn';
      btn.setAttribute('aria-label', '收藏此文献');
      btn.setAttribute('aria-pressed', this.store.has(link) ? 'true' : 'false');
      btn.textContent = this.store.has(link) ? '★' : '☆';
      btn.addEventListener('click', (e) => {
        e.preventDefault();
        e.stopPropagation();
        this._toggle(card, btn, link);
      });

      card.appendChild(btn);
      if (this.store.has(link)) card.classList.add('is-bookmarked');
    }

    _toggle(card, btn, link) {
      const meta = _extractMeta(card);
      const nowOn = this.store.toggle(link, meta);
      btn.setAttribute('aria-pressed', nowOn ? 'true' : 'false');
      btn.textContent = nowOn ? '★' : '☆';
      card.classList.toggle('is-bookmarked', nowOn);
      this._toast(nowOn ? '已收藏' : '已取消');
    }

    _toast(msg) {
      let t = document.querySelector('.bookmark-toast');
      if (!t) {
        t = document.createElement('div');
        t.className = 'bookmark-toast';
        document.body.appendChild(t);
      }
      t.textContent = msg;
      t.classList.add('show');
      clearTimeout(this._toastTimer);
      this._toastTimer = setTimeout(() => t.classList.remove('show'), 1500);
    }

    bindGestures(root = document) {
      const cards = root.querySelectorAll(CARD_SELECTORS.join(','));
      cards.forEach(card => this._bindGestures(card));
    }

    _bindGestures(card) {
      if (card.dataset.gestureBound === '1') return;
      card.dataset.gestureBound = '1';

      let pressTimer = null;
      let startX = 0, startY = 0;
      let triggered = false;
      const link = card.dataset.bookmarkKey;
      if (!link) return;

      const cancel = () => {
        if (pressTimer) { clearTimeout(pressTimer); pressTimer = null; }
      };

      const triggerToggle = () => {
        if (triggered) return;
        triggered = true;
        const btn = card.querySelector(':scope > .bookmark-btn');
        const meta = _extractMeta(card);
        const nowOn = this.store.toggle(link, meta);
        if (btn) {
          btn.setAttribute('aria-pressed', nowOn ? 'true' : 'false');
          btn.textContent = nowOn ? '★' : '☆';
        }
        card.classList.toggle('is-bookmarked', nowOn);
        if (navigator.vibrate) try { navigator.vibrate(30); } catch {}
        this._toast(nowOn ? '已收藏' : '已取消');
      };

      card.addEventListener('pointerdown', (e) => {
        if (e.target.closest && e.target.closest('.bookmark-btn,a')) return;
        startX = e.clientX; startY = e.clientY;
        triggered = false;
        pressTimer = setTimeout(() => {
          pressTimer = null;
          triggerToggle();
        }, 350);
      });

      card.addEventListener('pointermove', (e) => {
        if (!pressTimer && triggered) return;
        const dx = e.clientX - startX;
        const dy = e.clientY - startY;
        if (pressTimer && (Math.abs(dx) > 10 || Math.abs(dy) > 10)) cancel();
        if (!triggered && dx > 50 && Math.abs(dy) < 30) {
          cancel();
          triggerToggle();
        }
      });

      card.addEventListener('pointerup', cancel);
      card.addEventListener('pointercancel', cancel);
      card.addEventListener('pointerleave', cancel);
    }

    renderFab() {
      let fab = document.querySelector('.bookmark-fab');
      if (!fab) {
        fab = document.createElement('button');
        fab.type = 'button';
        fab.className = 'bookmark-fab';
        fab.setAttribute('aria-label', '我的收藏');
        fab.innerHTML = '<span class="bookmark-fab-icon">⭐</span><span class="bookmark-fab-label">收藏</span><span class="bookmark-fab-badge">0</span>';
        document.body.appendChild(fab);
        fab.addEventListener('click', () => this.openPanel());
      }
      const update = () => {
        const n = this.store.count();
        const badge = fab.querySelector('.bookmark-fab-badge');
        if (badge) badge.textContent = String(n);
        fab.classList.toggle('is-empty', n === 0);
      };
      update();
      document.addEventListener('bookmarkschange', update);
    }

    openPanel() {
      let panel = document.querySelector('.bookmark-panel');
      if (!panel) {
        panel = document.createElement('div');
        panel.className = 'bookmark-panel';
        panel.innerHTML = `
          <div class="bookmark-panel-overlay"></div>
          <div class="bookmark-panel-card">
            <div class="bookmark-panel-head">
              <h2 class="bookmark-panel-title">我的收藏 <span class="bookmark-panel-count">0</span></h2>
              <div class="bookmark-panel-actions">
                <button type="button" class="bookmark-export-btn" data-fmt="rss">RSS</button>
                <button type="button" class="bookmark-export-btn" data-fmt="md">MD</button>
                <button type="button" class="bookmark-export-btn" data-fmt="bib">BibTeX</button>
                <button type="button" class="bookmark-panel-close" aria-label="关闭">✕</button>
              </div>
            </div>
            <div class="bookmark-panel-body"></div>
          </div>
        `;
        document.body.appendChild(panel);
        panel.querySelector('.bookmark-panel-close').addEventListener('click', () => this._closePanel());
        panel.querySelector('.bookmark-panel-overlay').addEventListener('click', () => this._closePanel());
        panel.querySelectorAll('.bookmark-export-btn').forEach(b => {
          b.addEventListener('click', () => this._exportAs(b.dataset.fmt));
        });
      }
      this._renderPanelBody(panel);
      panel.classList.add('open');
    }

    _closePanel() {
      const panel = document.querySelector('.bookmark-panel');
      if (panel) panel.classList.remove('open');
    }

    _renderPanelBody(panel) {
      const body = panel.querySelector('.bookmark-panel-body');
      const countEl = panel.querySelector('.bookmark-panel-count');
      const list = this.store.list();
      countEl.textContent = `(${list.length})`;
      if (list.length === 0) {
        body.innerHTML = '<div class="bookmark-panel-empty"><p>还没有收藏任何文章。在日报/周报里点击 ☆ 或长按卡片即可。</p></div>';
        return;
      }
      const groups = {};
      for (const it of list) {
        const k = it.source_date || '其他';
        (groups[k] = groups[k] || []).push(it);
      }
      const keys = Object.keys(groups).sort((a, b) => (a < b ? 1 : a > b ? -1 : 0));
      const html = keys.map(k => {
        const items = groups[k].map(it => {
          const ttl = it.title_zh || it.title_en || it.link;
          const en = it.title_en && it.title_en !== it.title_zh ? `<div class="bookmark-panel-item-en">${_escapeHtml(it.title_en)}</div>` : '';
          const meta = [it.journal, _hostname(it.link)].filter(Boolean).join(' · ');
          return `
            <li class="bookmark-panel-item" data-link="${_escapeHtml(it.link)}">
              <a class="bookmark-panel-item-title" href="${_escapeHtml(it.link)}" target="_blank" rel="noopener noreferrer">${_escapeHtml(ttl)}</a>
              ${en}
              <div class="bookmark-panel-item-meta">${_escapeHtml(meta)}</div>
              <button type="button" class="bookmark-panel-item-remove" aria-label="删除">删</button>
            </li>`;
        }).join('');
        return `<section class="bookmark-panel-group"><h3>📅 ${_escapeHtml(k)} <span class="bookmark-panel-group-count">(${groups[k].length})</span></h3><ol>${items}</ol></section>`;
      }).join('');
      body.innerHTML = html;
      body.querySelectorAll('.bookmark-panel-item-remove').forEach(btn => {
        btn.addEventListener('click', (e) => {
          const li = e.target.closest('[data-link]');
          if (!li) return;
          const link = li.dataset.link;
          this.store.remove(link);
          this._renderPanelBody(panel);
          document.querySelectorAll(`[data-bookmark-key="${(window.CSS && CSS.escape ? CSS.escape(link) : link)}"]`).forEach(card => {
            card.classList.remove('is-bookmarked');
            const sb = card.querySelector(':scope > .bookmark-btn');
            if (sb) { sb.setAttribute('aria-pressed', 'false'); sb.textContent = '☆'; }
          });
        });
      });
    }

    _exportAs(fmt) {
      if (!window.BookmarkExports) {
        alert('exports.js 未加载');
        return;
      }
      const list = this.store.list();
      if (list.length === 0) { alert('收藏为空'); return; }
      const ymd = new Date().toISOString().slice(0, 10);
      const map = {
        rss: { fn: window.BookmarkExports.exportRSS, ext: 'xml', mime: 'application/rss+xml' },
        md:  { fn: window.BookmarkExports.exportMarkdown, ext: 'md', mime: 'text/markdown' },
        bib: { fn: window.BookmarkExports.exportBibTeX, ext: 'bib', mime: 'application/x-bibtex' },
      };
      const m = map[fmt];
      if (!m) return;
      const blob = m.fn(list);
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `bookmarks-${ymd}.${m.ext}`;
      document.body.appendChild(a);
      a.click();
      a.remove();
      setTimeout(() => URL.revokeObjectURL(url), 1000);
    }
  }

  window.BookmarkUI = BookmarkUI;
  window.BookmarkStore = BookmarkStore;

  function _autoInit() {
    if (window.__bookmarksInited) return;
    window.__bookmarksInited = true;
    const store = new BookmarkStore();
    const ui = new BookmarkUI(store);
    ui.attachToCards();
    ui.bindGestures();
    ui.renderFab();
    window.literatureBookmarks = { store, ui };
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', _autoInit);
  } else {
    _autoInit();
  }
})();
