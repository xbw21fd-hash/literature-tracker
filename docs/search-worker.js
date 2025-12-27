/**
 * Search Worker - 后台搜索处理
 */

// 简化的倒排索引搜索引擎(Worker版本)
class WorkerSearchEngine {
    constructor() {
        this.index = new Map();
        this.documents = new Map();
        this.stopWords = new Set([
            'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for',
            'of', 'with', 'by', 'from', 'as', 'is', 'was', 'are', 'were', 'been',
            'be', 'have', 'has', 'had', 'do', 'does', 'did'
        ]);
    }

    buildIndex(articles) {
        this.index.clear();
        this.documents.clear();

        articles.forEach(article => {
            this.documents.set(article.id, article);

            const text = [
                article.title || '',
                article.title_zh || '',
                article.abstract || '',
                article.abstract_zh || ''
            ].join(' ').toLowerCase();

            const words = this.tokenize(text);

            words.forEach(word => {
                if (!this.index.has(word)) {
                    this.index.set(word, new Set());
                }
                this.index.get(word).add(article.id);
            });
        });
    }

    tokenize(text) {
        const words = text.match(/\b[a-z]{4,}\b/g) || [];
        return words.filter(word => !this.stopWords.has(word));
    }

    search(query) {
        const words = this.tokenize(query.toLowerCase());
        if (words.length === 0) return [];

        const matchedIds = new Set();
        const wordScores = new Map();

        words.forEach(word => {
            const ids = this.index.get(word);
            if (ids) {
                ids.forEach(id => {
                    matchedIds.add(id);
                    wordScores.set(id, (wordScores.get(id) || 0) + 1);
                });
            }
        });

        const results = Array.from(matchedIds).map(id => {
            const article = this.documents.get(id);
            return {
                article,
                score: wordScores.get(id)
            };
        });

        results.sort((a, b) => b.score - a.score);
        return results.map(r => r.article);
    }
}

// 创建搜索引擎实例
const searchEngine = new WorkerSearchEngine();

// 处理消息
self.onmessage = function (e) {
    const { taskId, type, data } = e.data;

    try {
        let result;

        switch (type) {
            case 'buildIndex':
                searchEngine.buildIndex(data.articles);
                result = { success: true, message: 'Index built successfully' };
                break;

            case 'search':
                result = searchEngine.search(data.query);
                break;

            case 'sort':
                result = data.items.sort((a, b) => {
                    if (data.order === 'asc') {
                        return (a[data.field] || '').localeCompare(b[data.field] || '');
                    } else {
                        return (b[data.field] || '').localeCompare(a[data.field] || '');
                    }
                });
                break;

            default:
                throw new Error(`Unknown task type: ${type}`);
        }

        self.postMessage({ taskId, result });
    } catch (error) {
        self.postMessage({ taskId, error: error.message });
    }
};

// 通知主线程Worker已就绪
self.postMessage({ type: 'ready' });
