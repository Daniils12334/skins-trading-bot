const fs = require('fs');
const saveDir = './data/skinport-history';
const RATE_LIMIT = {
    REQUESTS_PER_WINDOW: 8,
    WINDOW_MS: 5 * 60 * 1000,
    lastRequestTime: 0,
    requestCount: 0
};

const delay = (ms) => new Promise(resolve => setTimeout(resolve, ms));

const saveToFile = (data, filename) => {
    try {
        if (!fs.existsSync(saveDir)) fs.mkdirSync(saveDir, { recursive: true });
        const filePath = `${saveDir}/${filename}`;
        fs.writeFileSync(filePath, JSON.stringify(data, null, 2));
        console.log(`✅ Данные сохранены в: ${filePath}`);
    } catch (error) {
        console.error('❌ Ошибка сохранения:', error.message);
    }
};

const fetchWithRateLimit = async (url, options) => {
    const now = Date.now();
    const timeSinceLastWindow = now - RATE_LIMIT.lastRequestTime;

    if (timeSinceLastWindow > RATE_LIMIT.WINDOW_MS) {
        RATE_LIMIT.requestCount = 0;
        RATE_LIMIT.lastRequestTime = now;
    }

    if (RATE_LIMIT.requestCount >= RATE_LIMIT.REQUESTS_PER_WINDOW) {
        const wait = RATE_LIMIT.WINDOW_MS - timeSinceLastWindow;
        console.log(`⏳ Лимит запросов. Ждём ${Math.ceil(wait / 1000)} секунд...`);
        await delay(wait + 1000);
        RATE_LIMIT.requestCount = 0;
        RATE_LIMIT.lastRequestTime = Date.now();
    }

    RATE_LIMIT.requestCount++;
    console.log(`📡 Выполняем запрос #${RATE_LIMIT.requestCount}/${RATE_LIMIT.REQUESTS_PER_WINDOW}`);

    const response = await fetch(url, options);

    if (response.status === 429) {
        const retryAfter = parseInt(response.headers.get('Retry-After') || '10') * 1000;
        console.warn(`⚠️ 429 Too Many Requests. Повтор через ${retryAfter / 1000} сек`);
        await delay(retryAfter);
        return fetchWithRateLimit(url, options);
    }

    if (!response.ok) {
        throw new Error(`HTTP error: ${response.status}`);
    }

    return response;
};

// 🔁 Главная функция
(async () => {
    try {
        const params = new URLSearchParams({
            app_id: 730,
            currency: 'EUR'
            // ❗ Не указываем market_hash_name — получим ВСЁ
        });

        const url = `https://api.skinport.com/v1/sales/history?${params.toString()}`;

        const response = await fetchWithRateLimit(url, {
            method: 'GET',
            headers: {
                'Accept-Encoding': 'br'
            }
        });

        const data = await response.json();
        console.log(`📦 Получено предметов: ${data.length}`);

        const timestamp = new Date().toISOString().replace(/[:.]/g, '-');
        const filename = `all_sales_history_${timestamp}.json`;

        saveToFile(data, filename);
    } catch (err) {
        console.error('💥 Ошибка:', err.message);
    }
})();
