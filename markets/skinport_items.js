const fs = require('fs');
const { Buffer } = require('buffer');

const clientId = 'dc907317e57e4481958fbd1f0c40031a';
const clientSecret = 'fPzfzlb3IQiB4URM0qnNHbBtuvkO7/ttNR0cyfb+AJNNVbK2fq/TjHxtdvP9PTi/qlfEg3TFyKS3B6ru9UvzUg==';
const credentials = `${clientId}:${clientSecret}`;
const encodedData = Buffer.from(credentials).toString('base64');
const authHeader = `Basic ${encodedData}`;
const saveDir = "./data/skinport-items";

const RATE_LIMIT = {
    REQUESTS_PER_MINUTE: 60,
    lastRequestTime: 0,
    requestCount: 0
};

const delay = (ms) => new Promise(resolve => setTimeout(resolve, ms));

const saveToFile = (data, filename) => {
    try {
        if (!fs.existsSync(saveDir)) fs.mkdirSync(saveDir, { recursive: true });
        const filePath = `${saveDir}/${filename}`;
        fs.writeFileSync(filePath, JSON.stringify(data, null, 2));
        console.log(`💾 Данные сохранены в: ${filePath}`);
    } catch (error) {
        console.error('❌ Ошибка сохранения файла:', error.message);
    }
};

const fetchWithRateLimit = async (url, options) => {
    const now = Date.now();
    const timeSinceLastRequest = now - RATE_LIMIT.lastRequestTime;

    if (timeSinceLastRequest > 60000) {
        RATE_LIMIT.requestCount = 0;
        RATE_LIMIT.lastRequestTime = now;
    }

    if (RATE_LIMIT.requestCount >= RATE_LIMIT.REQUESTS_PER_MINUTE) {
        const timeToWait = 61000 - timeSinceLastRequest;
        console.log(`⏳ Достигнут лимит. Ждём ${Math.ceil(timeToWait / 1000)} сек...`);
        await delay(timeToWait);
        RATE_LIMIT.requestCount = 0;
        RATE_LIMIT.lastRequestTime = Date.now();
    }

    RATE_LIMIT.requestCount++;
    console.log(`🌐 Запрос #${RATE_LIMIT.requestCount}/${RATE_LIMIT.REQUESTS_PER_MINUTE}`);

    const controller = new AbortController();
    const timeout = setTimeout(() => controller.abort(), 30000);

    try {
        const response = await fetch(url, {
            ...options,
            signal: controller.signal
        });

        clearTimeout(timeout);

        if (response.status === 429) {
            const retryAfter = parseInt(response.headers.get('Retry-After') || '10');
            console.warn(`⚠️  429 Too Many Requests. Повтор через ${retryAfter} сек...`);
            await delay(retryAfter * 1000);
            return fetchWithRateLimit(url, options);
        }

        if (!response.ok) {
            throw new Error(`HTTP error: ${response.status}`);
        }

        return response;

    } catch (error) {
        clearTimeout(timeout);
        if (error.name === 'AbortError') {
            console.error('🕓 Превышено время ожидания (30 сек)');
        } else {
            console.error('❌ Ошибка запроса:', error.message);
        }
        throw error;
    }
};

// 🚀 Основной запуск
(async () => {
    try {
        console.log("🚀 Запуск Skinport fetch");

        const params = new URLSearchParams({
            app_id: 730,
            currency: 'EUR',
            tradable: 0
        });

        const response = await fetchWithRateLimit(
            `https://api.skinport.com/v1/items?${params}`,
            {
                method: 'GET',
                headers: {
                    'Authorization': authHeader,
                    'Accept-Encoding': 'br'
                }
            }
        );

        const text = await response.text();
        let data;
        try {
            data = JSON.parse(text);
        } catch (e) {
            console.error("❌ Ошибка разбора JSON:", e.message);
            console.log("Ответ сервера:", text);
            process.exit(1);
        }

        console.log(`✅ Получено предметов: ${data.length}`);

        const timestamp = new Date().toISOString().replace(/[:.]/g, '-');
        const filename = `skinport_items_${timestamp}.json`;
        saveToFile(data, filename);

        console.log("✅ Скрипт успешно завершён.");
        process.exit(0);

    } catch (e) {
        console.error("🔥 Критическая ошибка:", e.message);
        process.exit(1);
    }
})();
