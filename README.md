# Location Facts Telegram Bot 🌍

Telegram-бот, который по геолокации пользователя отправляет интересные факты о близлежащих местах, используя OpenAI GPT-4.

## Функции ✨

- 📍 **Статическая локация**: Отправьте геолокацию и получите интересный факт о месте в радиусе 1 км
- 🔄 **Live Location**: Получайте новые факты каждые 10 минут при движении (автоматическое отслеживание)
- 🤖 **Интеллектуальные ответы**: Использует OpenAI GPT-4 для генерации уникальных фактов
- 🔄 **Fallback на OpenRouter**: Автоматический переход на OpenRouter при недоступности OpenAI API
- 🚀 **Быстрый деплой**: Автоматический деплой на Railway через GitHub Actions
- ⚡ **Оптимизация токенов**: Rate limiting и контроль расхода AI токенов

## Быстрый старт

### Локальная разработка

1. **Клонируйте репозиторий**
   ```bash
   git clone <repository-url>
   cd location-facts-bot
   ```

2. **Установите зависимости**
   ```bash
   pip install -r requirements.txt
   ```

3. **Настройте переменные окружения**
   
   Скопируйте `env_template.txt` в `.env` и заполните:
   ```
   TELEGRAM_TOKEN=your_telegram_bot_token_here
   OPENAI_API_KEY=your_openai_api_key_here
   OPENROUTER_API_KEY=your_openrouter_api_key_here
   ```
   
   Необходимо указать хотя бы один из ключей: OPENAI_API_KEY или OPENROUTER_API_KEY. Если указаны оба, система попробует сначала использовать OpenAI, а при неудаче перейдет на OpenRouter.

4. **Запустите бота**
   ```bash
   python main.py
   ```

### Получение токенов

#### Telegram Bot Token
1. Найдите [@BotFather](https://t.me/BotFather) в Telegram
2. Отправьте `/newbot` и следуйте инструкциям
3. Скопируйте токен из сообщения BotFather

#### OpenAI API Key
1. Зарегистрируйтесь на [OpenAI Platform](https://platform.openai.com/)
2. Перейдите в [API Keys](https://platform.openai.com/api-keys)
3. Создайте новый ключ и скопируйте его

#### OpenRouter API Key
1. Зарегистрируйтесь на [OpenRouter](https://openrouter.ai/)
2. Перейдите в настройки API Keys
3. Создайте новый ключ и скопируйте его

## Деплой на Railway

### Автоматический деплой

1. **Форк репозитория** на GitHub

2. **Создайте проект на Railway**
   - Зайдите на [Railway](https://railway.app/)
   - Подключите ваш GitHub репозиторий
   - Railway автоматически определит Python проект

3. **Настройте переменные окружения в Railway**
   - `TELEGRAM_TOKEN`: ваш токен Telegram бота
   - `OPENAI_API_KEY`: ваш ключ OpenAI API (опционально, если есть OPENROUTER_API_KEY)
   - `OPENROUTER_API_KEY`: ваш ключ OpenRouter API (опционально, если есть OPENAI_API_KEY)

4. **Настройте GitHub Secrets** (для автоматического деплоя):
   - `RAILWAY_TOKEN`: токен Railway (получите в настройках аккаунта)
   - `RAILWAY_PROJECT_ID`: ID проекта Railway

5. **Пуш в main ветку** автоматически задеплоит бота

### Ручной деплой

```bash
# Установите Railway CLI
npm install -g @railway/cli

# Войдите в аккаунт
railway login

# Задеплойте проект
railway up
```

## Использование 🎯

### Статическая локация
1. Найдите вашего бота в Telegram
2. Отправьте `/start` для получения инструкций
3. Отправьте геолокацию через скрепку → "Геопозиция"
4. Получите интересный факт о вашем местоположении!

### Live Location (новое в v1.1!)
1. Отправьте live-локацию (удерживайте кнопку геолокации → "Транслировать геопозицию")
2. Бот начнет отслеживание и отправит первый факт
3. Каждые 10 минут получайте новые факты о текущем местоположении
4. Отследжвание автоматически остановится по истечении времени или используйте `/stop`

## Команды бота

- `/start` - Приветствие и инструкции
- `/ping` - Проверка работоспособности и количество активных сессий
- `/stop` - Остановить все активные live-сессии
- 📍 **Геолокация** - Получить факт о месте
- 🔄 **Live Геолокация** - Начать отслеживание с периодическими фактами

## Архитектура

```
├── main.py                    # Основной файл бота с handlers
├── ai_client.py               # Универсальный клиент для работы с AI API
├── openai_client.py           # Клиент для работы с OpenAI API
├── openrouter_client.py       # Клиент для работы с OpenRouter API
├── live_location_manager.py   # Менеджер live-локаций и периодических задач
├── requirements.txt          # Python зависимости
├── Procfile                  # Конфигурация для Railway
├── railway.json              # Настройки Railway
└── .github/workflows/        # GitHub Actions для CI/CD
```

## Roadmap

### Version 1.0 ✅
- [x] Обработка статической геолокации
- [x] Интеграция с OpenAI GPT-4
- [x] Деплой на Railway
- [x] Базовое логирование

### Version 1.1 ✅
- [x] Поддержка Live Location
- [x] Периодическая отправка фактов (каждые 10 минут)
- [x] Управление сессиями и автоматическая очистка
- [x] Rate limiting для OpenAI API
- [x] Улучшенное логирование и обработка ошибок

### Version 1.2 ✅
- [x] Интеграция с OpenRouter как альтернативным AI провайдером
- [x] Автоматический fallback при недоступности OpenAI API
- [ ] Кэширование фактов для популярных мест
- [ ] Настройка языка ответа

### Version 1.3 💡
- [ ] Статистика использования
- [ ] Webhook режим вместо polling
- [ ] База данных для постоянного хранения сессий

## Технические детали

- **Backend**: Python 3.11, aiogram 3.x
- **AI**: OpenAI GPT-4-1106-preview, OpenRouter (Claude-3-Haiku и другие)
- **Deploy**: Railway с Nixpacks
- **CI/CD**: GitHub Actions
- **Session Management**: In-memory с автоматической очисткой
- **Rate Limiting**: 1 запрос в секунду к AI API
- **Live Location**: Периодические задачи с asyncio
- **Fault Tolerance**: Автоматический переход между AI-провайдерами

## Мониторинг

Бот логирует:
- Все входящие локации и запросы
- Использование OpenAI и OpenRouter токенов
- Переключения между AI-провайдерами
- Активные live-сессии
- Ошибки и исключения
- Метрики производительности

## Лицензия

MIT License - см. файл LICENSE

## Поддержка

Если у вас есть вопросы или предложения:
- Создайте Issue в репозитории
- Отправьте Pull Request

---

**Создано с ❤️ для изучения интересных мест мира!**

*Current Version: 1.2 - Добавлена поддержка OpenRouter как альтернативного AI-провайдера!* 