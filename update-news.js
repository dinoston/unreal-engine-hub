/**
 * update-news.js
 * 매일 자동으로 뉴스를 가져와 index.html을 업데이트하는 스크립트
 * 실행: node update-news.js
 * 자동화: Windows 작업 스케줄러로 매일 실행 설정 가능
 */

const https = require('https');
const fs = require('fs');
const path = require('path');

const NEWS_API_KEY = process.env.NEWS_API_KEY || ''; // .env 또는 환경변수에 설정
const INDEX_PATH = path.join(__dirname, 'index.html');

// 검색 쿼리 설정
const QUERIES = {
    us: 'autonomous driving simulation Unreal Engine NVIDIA Waymo',
    china: '自动驾驶 仿真 中国 OR autonomous driving simulation China',
    unreal: 'Unreal Engine autonomous vehicle simulation',
    assets: 'Fab marketplace free assets Unreal Engine',
    gis: 'Unreal Engine GIS geospatial simulation'
};

/**
 * NewsAPI에서 뉴스 가져오기
 */
function fetchNews(query, fromDate) {
    return new Promise((resolve, reject) => {
        if (!NEWS_API_KEY) {
            console.log('[SKIP] NEWS_API_KEY 없음 - 수동 업데이트 필요');
            resolve([]);
            return;
        }

        const params = new URLSearchParams({
            q: query,
            from: fromDate,
            sortBy: 'publishedAt',
            language: 'en',
            apiKey: NEWS_API_KEY,
            pageSize: 5
        });

        const url = `https://newsapi.org/v2/everything?${params}`;

        https.get(url, (res) => {
            let data = '';
            res.on('data', chunk => data += chunk);
            res.on('end', () => {
                try {
                    const json = JSON.parse(data);
                    if (json.status === 'ok') {
                        resolve(json.articles || []);
                    } else {
                        console.error('[API Error]', json.message);
                        resolve([]);
                    }
                } catch (e) {
                    reject(e);
                }
            });
        }).on('error', reject);
    });
}

/**
 * 날짜 포맷 (February 18, 2026 형식)
 */
function formatDate(dateStr) {
    const d = new Date(dateStr);
    return d.toLocaleDateString('en-US', { year: 'numeric', month: 'long', day: 'numeric' });
}

/**
 * 기사 배열로 카드 HTML 생성
 */
function buildCards(articles, emoji = '📰') {
    if (!articles.length) return '';

    return articles.map(a => {
        const title = (a.title || '').replace(/"/g, '&quot;').slice(0, 80);
        const desc = (a.description || a.content || '내용 없음').replace(/"/g, '&quot;').slice(0, 200);
        const date = formatDate(a.publishedAt);
        const source = a.source?.name || 'News';
        const url = a.url || '#';

        return `
                <div class="card fade-in">
                    <div class="card-image">${emoji}</div>
                    <div class="card-content">
                        <div class="card-meta">${date} · ${source}</div>
                        <h3 class="card-title">${title}</h3>
                        <p class="card-summary">${desc}</p>
                        <div class="card-footer">
                            <span class="card-tag">Latest News</span>
                            <a href="${url}" class="read-more" target="_blank">Read More</a>
                        </div>
                    </div>
                </div>`;
    }).join('\n');
}

/**
 * HTML 섹션 교체
 */
function replaceSection(html, sectionId, newCards) {
    const regex = new RegExp(
        `(<div id="${sectionId}" class="section[^"]*">.*?<div class="card-grid">)(.*?)(</div>\\s*</div>\\s*</div>)`,
        's'
    );
    return html.replace(regex, (match, open, _old, close) => {
        return open + '\n' + newCards + '\n            ' + close;
    });
}

/**
 * 마지막 업데이트 날짜 교체
 */
function updateLastModified(html) {
    const now = new Date();
    const dateStr = now.toLocaleDateString('en-US', { year: 'numeric', month: 'long', day: 'numeric' });
    return html.replace(
        /Last Updated: [^<]+/,
        `Last Updated: ${dateStr}`
    );
}

/**
 * 메인 실행
 */
async function main() {
    console.log('🔄 뉴스 업데이트 시작...');

    const twoWeeksAgo = new Date();
    twoWeeksAgo.setDate(twoWeeksAgo.getDate() - 14);
    const fromDate = twoWeeksAgo.toISOString().split('T')[0];

    console.log(`📅 검색 범위: ${fromDate} ~ 오늘`);

    try {
        // 뉴스 병렬 fetch
        const [usArticles, chinaArticles] = await Promise.all([
            fetchNews(QUERIES.us, fromDate),
            fetchNews(QUERIES.china, fromDate)
        ]);

        let html = fs.readFileSync(INDEX_PATH, 'utf-8');

        if (usArticles.length) {
            console.log(`🇺🇸 미국 뉴스 ${usArticles.length}건 업데이트`);
            const usCards = buildCards(usArticles, '🤖');
            html = replaceSection(html, 'us', usCards);
        }

        if (chinaArticles.length) {
            console.log(`🇨🇳 중국 뉴스 ${chinaArticles.length}건 업데이트`);
            const chinaCards = buildCards(chinaArticles, '🔬');
            html = replaceSection(html, 'china', chinaCards);
        }

        html = updateLastModified(html);
        fs.writeFileSync(INDEX_PATH, html, 'utf-8');

        console.log('✅ index.html 업데이트 완료!');
        console.log('');
        console.log('💡 뉴스API가 없으면 수동으로 내용을 업데이트하거나');
        console.log('   https://newsapi.org 에서 무료 API 키를 발급받으세요.');
        console.log('   발급 후: set NEWS_API_KEY=your_key_here');

    } catch (err) {
        console.error('❌ 업데이트 오류:', err.message);
    }
}

main();
