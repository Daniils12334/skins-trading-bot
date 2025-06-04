const fs = require('fs');
const { Buffer } = require('buffer');

const clientId = 'dc907317e57e4481958fbd1f0c40031a';
const clientSecret = 'fPzfzlb3IQiB4URM0qnNHbBtuvkO7/ttNR0cyfb+AJNNVbK2fq/TjHxtdvP9PTi/qlfEg3TFyKS3B6ru9UvzUg==';
const credentials = `${clientId}:${clientSecret}`;
const encodedData = Buffer.from(credentials).toString('base64');
const authHeader = `Basic ${encodedData}`;
const saveDir = "./data/skinport-items";

// Правильная конфигурация rate limit
const RATE_LIMIT = {
    REQUESTS_PER_MINUTE: 60,       // Skinport обычно позволяет 60 запросов в минуту
    lastRequestTime: 0,
    requestCount: 0
};

// Функция для создания задержки
const delay = (ms) => new Promise(resolve => setTimeout(resolve, ms));

// Функция сохранения данных
const saveToFile = (data, filename) => {
    try {
        if (!fs.existsSync(saveDir)) fs.mkdirSync(saveDir, { recursive: true });
        const filePath = `${saveDir}/${filename}`;
        fs.writeFileSync(filePath, JSON.stringify(data, null, 2));
        console.log(`Данные сохранены в: ${filePath}`);
        return true;
    } catch (error) {
        console.error('Ошибка сохранения:', error);
        return false;
    }
};

// Функция для выполнения запроса с учетом rate limit
const fetchWithRateLimit = async (url, options) => {
    const now = Date.now();
    const timeSinceLastRequest = now - RATE_LIMIT.lastRequestTime;
    
    // Если прошла минута - сбрасываем счетчик
    if (timeSinceLastRequest > 60000) {
        RATE_LIMIT.requestCount = 0;
        RATE_LIMIT.lastRequestTime = now;
    }
    
    // Если достигли лимита - ждем окончания минуты
    if (RATE_LIMIT.requestCount >= RATE_LIMIT.REQUESTS_PER_MINUTE) {
        const timeToWait = 61000 - timeSinceLastRequest; // +1 сек для надежности
        console.log(`Достигнут лимит запросов. Ожидание ${Math.ceil(timeToWait/1000)} секунд...`);
        await delay(timeToWait);
        
        // Сбрасываем счетчик после ожидания
        RATE_LIMIT.requestCount = 0;
        RATE_LIMIT.lastRequestTime = Date.now();
    }
    
    // Увеличиваем счетчик запросов
    RATE_LIMIT.requestCount++;
    console.log(`Запрос #${RATE_LIMIT.requestCount}/${RATE_LIMIT.REQUESTS_PER_MINUTE}`);
    
    try {
        const controller = new AbortController();
        const timeoutId = setTimeout(() => controller.abort(), 30000);
        
        const response = await fetch(url, {
            ...options,
            signal: controller.signal
        });
        
        clearTimeout(timeoutId);
        
        if (response.status === 429) {
            const retryAfter = parseInt(response.headers.get('Retry-After') || '10');
            console.log(`Получена 429 ошибка. Повтор через ${retryAfter} секунд...`);
            await delay(retryAfter * 1000);
            return fetchWithRateLimit(url, options);
        }
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        return response;
    } catch (error) {
        if (error.name === 'AbortError') {
            console.error('Таймаут запроса (30 секунд)');
        }
        throw error;
    }
};

// Основная функция
(async () => {
    try {
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
        
        // Получаем данные
        const data = await response.json();
        console.log(`Получено ${data.length} элементов`);
        
        // Генерация имени файла
        const timestamp = new Date().toISOString().replace(/[:.]/g, '-');
        const filename = `skinport_items_${timestamp}.json`;
        
        // Сохранение в файл
        saveToFile(data, filename);
        
        console.log('Запрос успешно выполнен!');
        
    } catch (error) {
        console.error('Критическая ошибка:', error.message);
    }
})();