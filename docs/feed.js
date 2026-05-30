/**
 * FeedUI — TikTok-style full-screen literature feed.
 * Renders one full-screen card per paper, with concept-poster overlay for APS
 * items, a sticky category filter bar, and reuses BookmarkUI / LikeUI for the
 * ⭐ / ❤️ buttons. Dependency-free vanilla JS.
 */
(function () {
  'use strict';

  const POSTER_ROWS = ['研究问题', '创新方法', '工作流程', '关键结果', '应用价值'];
  const ALL_CAT = '全部';

  function esc(s) {
    const d = document.createElement('div');
    d.textContent = (s == null ? '' : String(s));
    return d.innerHTML;
  }

  function el(tag, cls, html) {
    const n = document.createElement(tag);
    if (cls) n.className = cls;
    if (html != null) n.innerHTML = html;
    return n;
  }

  function buildPosterFigure(item) {
    const fig = el('div', 'poster-figure');
    const img = document.createElement('img');
    img.loading = 'lazy';
    img.src = item.image;
    img.alt = item.title_zh || item.title_en || '';
    img.setAttribute('onerror', "this.style.display='none'");
    fig.appendChild(img);

    if (item.poster_elements && typeof item.poster_elements === 'object') {
      const overlay = el('div', 'poster-overlay');
      let rows = 0;
      POSTER_ROWS.forEach(function (key) {
        const val = item.poster_elements[key];
        if (val == null || val === '') return;
        const row = el('div', 'poster-row',
          '<b>' + esc(key) + '</b>' + esc(val));
        overlay.appendChild(row);
        rows++;
      });
      if (rows > 0) fig.appendChild(overlay);
    }
    return fig;
  }

  function buildCard(item) {
    const card = el('article', 'feed-card');
    card.dataset.bookmarkKey = item.link || '';
    card.dataset.category = item.category || '';

    if (item.category) {
      card.appendChild(el('span', 'cat-tag', esc(item.category)));
    }

    const h = el('h2', 'feed-title-zh');
    h.textContent = item.title_zh || item.title_en || '';
    card.appendChild(h);

    if (item.summary) {
      card.appendChild(el('p', 'summary', esc(item.summary)));
    }

    if (item.image) {
      card.appendChild(buildPosterFigure(item));
    }

    if (item.link) {
      const a = el('a', 'src-link');
      a.href = item.link;
      a.target = '_blank';
      a.rel = 'noopener noreferrer';
      a.textContent = '查看原文 ↗';
      card.appendChild(a);
    }

    if (item.source === 'APS' && item.deep_analysis) {
      const details = el('details', 'deep-details');
      details.appendChild(el('summary', null, '展开精读'));
      const body = el('div', 'deep-body');
      body.textContent = item.deep_analysis;
      details.appendChild(body);
      card.appendChild(details);
    }

    return card;
  }

  function renderFeed(items, container) {
    if (!container) return;
    container.innerHTML = '';
    (items || []).forEach(function (item) {
      container.appendChild(buildCard(item));
    });
    if (window.BookmarkUI && window.literatureBookmarks && window.literatureBookmarks.ui) {
      window.literatureBookmarks.ui.attachToCards(container);
    } else if (window.BookmarkUI && window.BookmarkStore) {
      new window.BookmarkUI(new window.BookmarkStore()).attachToCards(container);
    }
    if (window.LikeUI && window.likeStore) {
      new window.LikeUI(window.likeStore).attachToCards(container);
    }
  }

  function distinctCategories(items) {
    const seen = [];
    (items || []).forEach(function (it) {
      const c = it && it.category;
      if (c && seen.indexOf(c) === -1) seen.push(c);
    });
    return seen;
  }

  function buildCatBar(items, barEl) {
    const bar = barEl || document.getElementById('cat-bar');
    if (!bar) return null;
    bar.innerHTML = '';
    const cats = [ALL_CAT].concat(distinctCategories(items));
    cats.forEach(function (cat, i) {
      const chip = el('button', 'chip');
      chip.type = 'button';
      chip.textContent = cat;
      chip.dataset.cat = cat;
      if (i === 0) chip.classList.add('active');
      chip.addEventListener('click', function () {
        bar.querySelectorAll('.chip').forEach(function (c) {
          c.classList.toggle('active', c === chip);
        });
        filterByCategory(cat);
      });
      bar.appendChild(chip);
    });
    return bar;
  }

  function filterByCategory(cat) {
    const showAll = (cat == null || cat === ALL_CAT);
    document.querySelectorAll('.feed-card').forEach(function (card) {
      const match = showAll || card.dataset.category === cat;
      card.classList.toggle('hidden', !match);
    });
  }

  function loadFeed() {
    const main = document.getElementById('feed');
    const bar = document.getElementById('cat-bar');
    if (!main) return;
    fetch('data/feed.json')
      .then(function (r) {
        if (!r.ok) throw new Error('HTTP ' + r.status);
        return r.json();
      })
      .then(function (data) {
        const items = (data && data.items) || [];
        if (!items.length) {
          main.innerHTML = '<div class="feed-empty">暂无文献，请稍后再来 ✨</div>';
          return;
        }
        renderFeed(items, main);
        buildCatBar(items, bar);
      })
      .catch(function (err) {
        console.warn('[feed] load failed:', err);
        main.innerHTML = '<div class="feed-empty">无法加载文献流，请稍后重试。</div>';
      });
  }

  window.FeedUI = {
    renderFeed: renderFeed,
    buildCatBar: buildCatBar,
    filterByCategory: filterByCategory,
    loadFeed: loadFeed,
  };

  function _autoInit() {
    if (window.__feedInited) return;
    if (!document.getElementById('feed')) return;
    window.__feedInited = true;
    loadFeed();
  }

  if (typeof document !== 'undefined') {
    if (document.readyState === 'loading') {
      document.addEventListener('DOMContentLoaded', _autoInit);
    } else {
      _autoInit();
    }
  }
})();
