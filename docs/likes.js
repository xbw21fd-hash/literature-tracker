/**
 * Likes for literature-tracker (mobile-friendly heart + export).
 * Storage: localStorage key "literature_likes", value = { [link]: meta }.
 * Mirrors bookmarks.js structure — no legacy migration needed.
 */
(function () {
  'use strict';
  const STORAGE_KEY = 'literature_likes';

  class LikeStore {
    constructor() {
      this.data = this._load();
    }

    _load() {
      try {
        const raw = (typeof localStorage !== 'undefined') && localStorage.getItem(STORAGE_KEY);
        return raw ? JSON.parse(raw) : {};
      } catch (e) {
        console.warn('[likes] failed to load:', e);
        return {};
      }
    }

    _save() {
      try {
        if (typeof localStorage !== 'undefined') {
          localStorage.setItem(STORAGE_KEY, JSON.stringify(this.data));
        }
      } catch (e) {
        console.warn('[likes] failed to save:', e);
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
        if (typeof window !== 'undefined') {
          window.dispatchEvent(new CustomEvent('likeschange', {
            detail: { count: this.count() }
          }));
        }
      } catch {}
    }
  }

  // --- UI ---

  const CARD_SELECTORS = [
    '.daily-paper-card',
    '.daily-news-item',
    '.daily-core-card',
    '.weekly-core-card',
    '.weekly-paper-card',
    '.daily-deep-card',
    '.feed-card',
  ];

  function _text(node) {
    return node ? node.textContent.replace(/\s+/g, ' ').trim() : '';
  }

  function _extractMeta(card) {
    const titleZhEl =
      card.querySelector('.daily-paper-title-zh, .daily-news-title-zh, .daily-core-title-zh, .weekly-core-title-zh, .daily-deep-title-zh, .feed-title-zh');
    const titleEnEl =
      card.querySelector('.daily-paper-title-en, .daily-news-title-en, .daily-core-title-en, .weekly-core-title-en, .daily-deep-title-en, .feed-title-en');
    let title_zh = _text(titleZhEl).replace(/#$/, '').trim();
    let title_en = _text(titleEnEl).replace(/#$/, '').trim();

    let journal = '';
    const chip = card.querySelector('.daily-chip-journal, .weekly-chip-journal, .weekly-chip');
    if (chip) {
      const t = _text(chip).replace(/^📖\s*/, '');
      journal = t.split(/[/·]/)[0].trim();
    }

    let source_type = 'daily';
    if (/weekly-/.test(card.className)) source_type = 'weekly';
    let source_date = '';
    const dateMatch = (typeof location !== 'undefined') && location.pathname.match(/(\d{4}-\d{2}-\d{2})\.html/);
    if (dateMatch) source_date = dateMatch[1];

    return { title_zh, title_en, journal, source_type, source_date };
  }

  class LikeUI {
    constructor(store) {
      this.store = store;
    }

    attachToCards(root) {
      if (!root || typeof root.querySelectorAll !== 'function') return;
      const cards = root.querySelectorAll(CARD_SELECTORS.join(','));
      cards.forEach(card => this._attach(card));
    }

    _attach(card) {
      if (card.querySelector(':scope > .like-btn')) return;
      const link = card.dataset.bookmarkKey ||
        (card.querySelector('a[href]') && card.querySelector('a[href]').href) || '';
      if (!link) return;

      const btn = document.createElement('button');
      btn.type = 'button';
      btn.className = 'like-btn';
      btn.setAttribute('aria-label', '喜欢此文献');
      btn.setAttribute('data-like-key', link);
      btn.setAttribute('aria-pressed', this.store.has(link) ? 'true' : 'false');
      btn.textContent = this.store.has(link) ? '❤️' : '🤍';

      btn.addEventListener('click', (e) => {
        e.preventDefault();
        e.stopPropagation();
        const meta = _extractMeta(card);
        const nowOn = this.store.toggle(link, meta);
        btn.setAttribute('aria-pressed', nowOn ? 'true' : 'false');
        btn.textContent = nowOn ? '❤️' : '🤍';
        card.classList.toggle('is-liked', nowOn);
      });

      card.appendChild(btn);
      if (this.store.has(link)) card.classList.add('is-liked');
    }
  }

  // Expose globals
  window.LikeStore = LikeStore;
  window.LikeUI = LikeUI;
  window.likeStore = new LikeStore();

  // Auto-init on DOMContentLoaded (guarded)
  function _autoInit() {
    if (window.__likesInited) return;
    window.__likesInited = true;
    const ui = new LikeUI(window.likeStore);
    ui.attachToCards(document);
    window.literatureLikes = { store: window.likeStore, ui };
  }

  if (typeof document !== 'undefined') {
    if (document.readyState === 'loading') {
      document.addEventListener('DOMContentLoaded', _autoInit);
    } else {
      _autoInit();
    }
  }
})();
