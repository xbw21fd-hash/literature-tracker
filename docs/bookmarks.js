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
  }

  window.BookmarkUI = BookmarkUI;
  window.BookmarkStore = BookmarkStore;
})();
