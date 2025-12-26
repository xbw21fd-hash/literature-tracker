// 文献追踪系统 - 前端应用

let allArticles = [];
let filteredArticles = [];
let favorites = new Set();
let currentPage = 1;
const PAGE_SIZE = 30;

// 初始化
document.addEventListener('DOMContentLoaded', () => {
    loadFavorites();
    loadArticles();
    setupSearch();
});

// 加载收藏
function loadFavorites() {
    const saved = localStorage.getItem('literature_favorites');
    if (saved) {
        favorites = new Set(JSON.parse(saved));
    }
}

// 保存收藏
function saveFavorites() {
    localStorage.setItem('literature_favorites', JSON.stringify([...favorites]));
}

// 加载文献数据
async function loadArticles() {
    try {
        const response = await fetch('data/index.json');
        const data = await response.json();
        
        allArticles = data.articles || [];
        
        // 合并本地收藏状态
        allArticles.forEach(article => {
            article.is_favorite = favorites.has(article.id);
        });
        
        updateStats(data);
        filterArticles();
    } catch (error) {
        console.error('加载数据失败:', error);
        document.getElementById('articleList').innerHTML = `
            <div class="no-results">
                <h3>暂无数据</h3>
                <p>请先运行抓取脚本获取文献</p>
            </div>
        `;
    }
}

// 更新统计信息
function updateStats(data) {
    document.getElementById('totalCount').textContent = data.total || 0;
    document.getElementById('favCount').textContent = favorites.size;
    
    if (data.last_update) {
        const date = new Date(data.last_update);
        document.getElementById('lastUpdate').textContent = date.toLocaleString('zh-CN');
    }
}

// 设置搜索
function setupSearch() {
    const input = document.getElementById('searchInput');
    let timeout;
    
    input.addEventListener('input', () => {
        clearTimeout(timeout);
        timeout = setTimeout(filterArticles, 300);
    });
    
    input.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') {
            filterArticles();
        }
    });
}

// 清除搜索
function clearSearch() {
    document.getElementById('searchInput').value = '';
    filterArticles();
}

// 筛选文献
function filterArticles() {
    const searchTerm = document.getElementById('searchInput').value.toLowerCase();
    const favoritesOnly = document.getElementById('favoritesOnly').checked;
    
    filteredArticles = allArticles.filter(article => {
        if (favoritesOnly && !article.is_favorite) {
            return false;
        }
        
        if (searchTerm) {
            const searchText = [
                article.title,
                article.title_zh,
                article.abstract,
                article.abstract_zh,
                article.journal,
                ...(article.authors || [])
            ].join(' ').toLowerCase();
            
            if (!searchText.includes(searchTerm)) {
                return false;
            }
        }
        
        return true;
    });
    
    currentPage = 1;
    sortArticles();
}

// 排序文献
function sortArticles() {
    const sortBy = document.getElementById('sortSelect').value;
    
    filteredArticles.sort((a, b) => {
        switch (sortBy) {
            case 'date-desc':
                return (b.pub_date || '').localeCompare(a.pub_date || '');
            case 'date-asc':
                return (a.pub_date || '').localeCompare(b.pub_date || '');
            case 'journal':
                return (a.journal || '').localeCompare(b.journal || '');
            default:
                return 0;
        }
    });
    
    renderArticles();
}

// 获取当前页数据
function getCurrentPageArticles() {
    const start = (currentPage - 1) * PAGE_SIZE;
    const end = start + PAGE_SIZE;
    return filteredArticles.slice(start, end);
}

// 获取总页数
function getTotalPages() {
    return Math.ceil(filteredArticles.length / PAGE_SIZE);
}

// 渲染文献列表
function renderArticles() {
    const container = document.getElementById('articleList');
    
    if (filteredArticles.length === 0) {
        container.innerHTML = `
            <div class="no-results">
                <h3>没有找到文献</h3>
                <p>尝试调整搜索条件</p>
            </div>
        `;
        renderPagination();
        return;
    }
    
    const pageArticles = getCurrentPageArticles();
    container.innerHTML = pageArticles.map(article => createArticleCard(article)).join('');
    renderPagination();
}

// 渲染分页
function renderPagination() {
    const totalPages = getTotalPages();
    const paginationContainer = document.getElementById('pagination');
    
    if (!paginationContainer) return;
    
    if (totalPages <= 1) {
        paginationContainer.innerHTML = '';
        return;
    }
    
    let html = '<div class="pagination">';
    
    // 上一页
    html += `<button class="page-btn" onclick="goToPage(${currentPage - 1})" ${currentPage === 1 ? 'disabled' : ''}>上一页</button>`;
    
    // 页码
    const maxVisible = 5;
    let startPage = Math.max(1, currentPage - Math.floor(maxVisible / 2));
    let endPage = Math.min(totalPages, startPage + maxVisible - 1);
    
    if (endPage - startPage < maxVisible - 1) {
        startPage = Math.max(1, endPage - maxVisible + 1);
    }
    
    if (startPage > 1) {
        html += `<button class="page-btn" onclick="goToPage(1)">1</button>`;
        if (startPage > 2) html += '<span class="page-ellipsis">...</span>';
    }
    
    for (let i = startPage; i <= endPage; i++) {
        html += `<button class="page-btn ${i === currentPage ? 'active' : ''}" onclick="goToPage(${i})">${i}</button>`;
    }
    
    if (endPage < totalPages) {
        if (endPage < totalPages - 1) html += '<span class="page-ellipsis">...</span>';
        html += `<button class="page-btn" onclick="goToPage(${totalPages})">${totalPages}</button>`;
    }
    
    // 下一页
    html += `<button class="page-btn" onclick="goToPage(${currentPage + 1})" ${currentPage === totalPages ? 'disabled' : ''}>下一页</button>`;
    
    // 页码信息
    html += `<span class="page-info">第 ${currentPage}/${totalPages} 页，共 ${filteredArticles.length} 篇</span>`;
    
    html += '</div>';
    paginationContainer.innerHTML = html;
}

// 跳转页面
function goToPage(page) {
    const totalPages = getTotalPages();
    if (page < 1 || page > totalPages) return;
    
    currentPage = page;
    renderArticles();
    window.scrollTo({ top: 0, behavior: 'smooth' });
}

// 创建文献卡片
function createArticleCard(article) {
    const authors = (article.authors || []).slice(0, 3).join(', ');
    const authorsMore = article.authors && article.authors.length > 3 ? ' et al.' : '';
    const isFav = article.is_favorite;
    
    return `
        <div class="article-card ${isFav ? 'favorite' : ''}" id="article-${article.id}">
            <div class="article-header">
                <h2 class="article-title">
                    <a href="${article.link}" target="_blank" rel="noopener">${escapeHtml(article.title_zh || article.title)}</a>
                </h2>
                <button class="favorite-btn" onclick="toggleFavorite('${article.id}')" title="${isFav ? '取消收藏' : '添加收藏'}">
                    ${isFav ? '⭐' : '☆'}
                </button>
            </div>
            
            <div class="article-meta">
                <span>📖 ${escapeHtml(article.journal || '未知期刊')}</span>
                <span>📅 ${article.pub_date || '未知日期'}</span>
                <span>👤 ${escapeHtml(authors + authorsMore) || '未知作者'}</span>
            </div>
            
            ${article.abstract_zh ? `
                <div class="article-abstract-zh" id="abstract-zh-${article.id}">
                    ${escapeHtml(article.abstract_zh)}
                </div>
            ` : ''}
        </div>
    `;
}

// 切换收藏
function toggleFavorite(id) {
    if (favorites.has(id)) {
        favorites.delete(id);
    } else {
        favorites.add(id);
    }
    
    saveFavorites();
    
    const article = allArticles.find(a => a.id === id);
    if (article) {
        article.is_favorite = favorites.has(id);
    }
    
    document.getElementById('favCount').textContent = favorites.size;
    
    if (document.getElementById('favoritesOnly').checked) {
        filterArticles();
    } else {
        const card = document.getElementById(`article-${id}`);
        if (card) {
            card.classList.toggle('favorite');
            const btn = card.querySelector('.favorite-btn');
            btn.innerHTML = favorites.has(id) ? '⭐' : '☆';
            btn.title = favorites.has(id) ? '取消收藏' : '添加收藏';
        }
    }
}

// HTML转义
function escapeHtml(text) {
    if (!text) return '';
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}
