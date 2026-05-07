# AI-ba-agent

**Бизнес-аналитик-Корпоративный архитектор** — AI-агент для извлечения требований к ПО из неструктурированных данных.

## Что делает агент

Принимает на вход: протоколы встреч, письма, интервью с заказчиком.  
Выдаёт: структурированные требования по методологии **Volere v16** в формате JSON.

### Конвейер обработки (6 этапов)
1. **Извлечение кандидатов** — разбивка текста на смысловые фрагменты `[SRC-N]`
2. **Классификация** — типы по Volere: BR, FR, NFR-PERF, NFR-SECU, CON, ARCH и др.
3. **Нормализация EARS** — атомарные утверждения: Ubiquitous / Event-driven / State-driven / Unwanted behaviour / Optional feature
4. **Проверка качества BABOK v3** — 8 атрибутов: корректность, полнота, непротиворечивость и др.
5. **Уточняющие вопросы** — интерактивный диалог для заполнения пробелов
6. **Финальный Volere JSON** — документ по схеме Volere ReqSpec v16

## Стек

- **Backend**: Python, FastAPI, LangChain
- **Frontend**: Vanilla JavaScript (SPA)
- **LLM**: OpenAI (default), GigaChat, Anthropic, Ollama

## Быстрый старт

### 1. Клонировать репозиторий
```bash
git clone https://github.com/asinitsyn91/ai-ba-agent.git
cd ai-ba-agent
```

### 2. Настроить окружение
```bash
cp backend/.env.example backend/.env
# Отредактировать backend/.env — указать LLM_PROVIDER и ключ API
```

### 3. Запустить
```bash
chmod +x start.sh
./start.sh
```

- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- Swagger docs: http://localhost:8000/docs

## Конфигурация LLM

В файле `backend/.env`:

```env
# Выбрать провайдера: openai | gigachat | anthropic | ollama
LLM_PROVIDER=gigachat

# GigaChat (base64-encoded "client_id:secret")
GIGACHAT_CREDENTIALS=ваш_base64_credential
GIGACHAT_SCOPE=GIGACHAT_API_PERS
GIGACHAT_MODEL=GigaChat-Pro
```

### Получение GigaChat credentials
1. Зарегистрироваться на [developers.sber.ru](https://developers.sber.ru/studio)
2. Создать проект, получить Client ID и Secret
3. Закодировать: `echo -n "client_id:secret" | base64`

## API

| Метод | Путь | Описание |
|---|---|---|
| POST | `/api/v1/analyze` | Запустить анализ текста (этапы 1-5) |
| POST | `/api/v1/clarify` | Применить ответы на уточняющие вопросы |
| POST | `/api/v1/finalize` | Сформировать финальный Volere JSON (этап 6) |
| GET | `/api/v1/session/{id}` | Получить данные сессии |
| GET | `/api/v1/health` | Healthcheck |

## Структура проекта

```
ai-ba-agent/
├── backend/
│   ├── app/
│   │   ├── api/routes.py          # REST endpoints
│   │   ├── core/
│   │   │   ├── config.py          # Настройки (pydantic-settings)
│   │   │   └── llm_factory.py     # Фабрика LLM-провайдеров
│   │   ├── models/schemas.py      # Pydantic-схемы
│   │   ├── prompts/               # Промпты для каждого этапа
│   │   ├── services/
│   │   │   ├── pipeline.py        # 6-этапный конвейер
│   │   │   └── session_store.py   # Хранилище сессий
│   │   └── main.py
│   ├── requirements.txt
│   └── .env.example
├── frontend/
│   ├── public/
│   │   ├── index.html
│   │   └── styles.css
│   └── src/
│       ├── main.js                # SPA приложение
│       └── api/client.js          # HTTP-клиент
├── references/                    # Методологические материалы
│   ├── skill_algorithm.md
│   ├── volere_requirements_schema.json
│   ├── babok_quality_checklist.md
│   └── ears_patterns.md
└── start.sh
```
