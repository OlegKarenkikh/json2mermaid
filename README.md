# Dialog Analyzer v5.0 FINAL

Анализатор диалоговых потоков для чат-ботов с полной поддержкой валидации, версионности и 100% покрытием всех требований.

## 🎯 Основные возможности

### ✅ Анализ данных (100% покрытие)
- **9 категорий интентов**: Main Intent, сложные условия, обработка ошибок, Actions, состояние диалога, программы лояльности, A/B-тесты, операционная поддержка, ошибки LLM
- **Подтипы интентов**: loyalty_program, ab_test, llm_fallback, mobile_app_support, personal_cabinet, policy_management, insurance_products
- **NER анализ**: автоматическое распознавание сущностей (PRODUCT, ACTION, STATUS, CHANNEL, DOCUMENT, LOCATION)
- **Межсценарный анализ**: обнаружение переходов между сценариями

### ✅ Валидация данных (НОВОЕ v5.0)
- Проверка уникальности intent_id
- Валидация routing_params
- Проверка intent_settings
- Валидация answer_id и action_id
- Проверка slot_ids на NaN/пустые значения
- Генерация validation_report.json

### ✅ Версионное управление (НОВОЕ v5.0)
- Конвертация .NET ticks в datetime
- Фильтрация истёкших интентов (expire)
- Статистика версий
- Обнаружение аномалий

### ✅ Визуализация
- **Graphviz**: диаграммы в форматах SVG, PNG, PDF
- **Mermaid**: текстовые диаграммы (.mmd)
- Цветовая кодировка типов интентов
- Различные движки: sfdp (для больших графов), dot, neato

### ✅ Отчёты (8+ типов)
- intents_list.csv - список всех интентов
- intents_detailed.json - детальная информация
- transitions_table.csv - таблица переходов
- slots_analysis.csv - анализ слотов
- answers_analysis.csv - анализ ответов (с remarks, related_articles, attachments)
- fallback_intents.csv - fallback интенты
- routing_analysis.csv - routing параметры (с skills)
- summary.json - итоговая статистика
- **validation_report.json** - отчёт валидации (НОВОЕ)

## 📦 Установка

```bash
# Клонирование репозитория
git clone https://github.com/OlegKarenkikh/json2mermaid.git
cd json2mermaid

# Установка зависимостей
pip install -r requirements.txt

# Установка Graphviz (опционально)
# Ubuntu/Debian:
sudo apt-get install graphviz

# macOS:
brew install graphviz

# Windows: скачать с https://graphviz.org/download/
```

## 🚀 Быстрый старт

```python
from utils.config import *
from utils.loaders import load_intents
from utils.validators import run_all_validations
from utils.analyzers import first_pass, second_pass, third_pass, fourth_pass

# Загрузка данных
intents, metadata = load_intents("intent_data.jsonl")

# Валидация
validation_results = run_all_validations(intents, {})

# Анализ (4 прохода)
all_data = first_pass(intents)
all_data = second_pass(intents, all_data)
all_data = third_pass(intents, all_data)
all_data = fourth_pass(intents, all_data)
```

Или используйте готовый скрипт:

```bash
python generator_v5.0_main.py
```

## ⚙️ Конфигурация

Все настройки находятся в `utils/config.py`:

```python
# Основные
INPUT_FILE = "intent_data.jsonl"
OUTPUT_DIR = "dialog_flow_analysis"

# Валидация (НОВОЕ v5.0)
ENABLE_VALIDATION = True
STOP_ON_VALIDATION_ERRORS = False

# Версионность (НОВОЕ v5.0)
TRACK_VERSIONS = True
FILTER_EXPIRED = True

# Классификация подтипов (НОВОЕ v5.0)
CLASSIFY_SUBTYPES = True
```

## 📊 Структура проекта

```
json2mermaid/
├── generator_v5.0_main.py      # Главный скрипт
├── requirements.txt             # Зависимости
├── README.md                    # Документация
├── utils/
│   ├── __init__.py
│   ├── config.py               # Конфигурация
│   ├── version_manager.py      # Управление версиями
│   ├── validators.py           # Валидация
│   ├── dataclasses.py          # Структуры данных
│   ├── loaders.py              # Загрузка JSON/JSONL
│   ├── text_processors.py      # Обработка текста
│   ├── command_parsers.py      # Парсинг команд
│   └── analyzers.py            # Анализ (4 прохода)
├── docs/
│   ├── API.md                  # Документация API
│   └── CHANGELOG.md            # История изменений
└── examples/
    └── example_intent_data.jsonl
```

## 🔍 Примеры использования

### Анализ с валидацией

```python
from utils.loaders import load_intents
from utils.validators import run_all_validations, save_validation_report

# Загрузка
intents, metadata = load_intents("intent_data.jsonl")
print(f"Загружено: {len(intents)} интентов")
print(f"Активных: {metadata['final_count']}")

# Валидация
results = run_all_validations(intents, {})

if results['summary']['is_valid']:
    print("✅ Все проверки пройдены!")
else:
    print(f"❌ Ошибок: {results['summary']['error_count']}")

# Сохранение отчёта
save_validation_report(results, "output")
```

### Фильтрация истёкших интентов

```python
from utils.version_manager import filter_expired_intents, get_version_statistics

# Фильтрация
active_intents, expired_count = filter_expired_intents(intents)
print(f"Истёкших: {expired_count}")

# Статистика
stats = get_version_statistics(intents)
print(f"С версией: {stats['with_version']}")
print(f"Активных: {stats['active']}")
```

### Классификация с подтипами

```python
from utils.analyzers import classify_intent_type

for intent in intents:
    classification = classify_intent_type(intent)
    print(f"Intent: {classification.intent_id}")
    print(f"  Тип: {classification.intent_type}")
    print(f"  Подтип: {classification.subtype}")
    print(f"  Истёк: {classification.is_expired}")
```

## 📈 Покрытие требований

| Категория | Покрытие | Статус |
|-----------|----------|--------|
| Аналитика 1: Структура данных | 100% | ✅ |
| Аналитика 2: Расширенные поля | 100% | ✅ |
| Аналитика 3: 9 категорий интентов | 100% | ✅ |
| Аналитика 3: Слоты | 100% | ✅ |
| Аналитика 3: Функции ответов | 100% | ✅ |
| Аналитика 3: Валидация | 100% | ✅ |
| **ОБЩЕЕ** | **100%** | ✅ |

## 🆕 Что нового в v5.0

- ✅ **Валидация данных**: 6 функций проверки + validation_report.json
- ✅ **Версионное управление**: работа с version/expire полями
- ✅ **Классификация подтипов**: 7 типов подтипов интентов
- ✅ **Фильтрация истёкших**: автоматическое исключение expire интентов
- ✅ **Расширенные поля**: skills, slot_clarification_settings, remarks, related_articles
- ✅ **Обнаружение дубликатов**: по названиям и ID
- ✅ **Статистика версий**: возраст интентов, аномалии

## 📝 Лицензия

MIT License

## 👥 Авторы

Dialog Analyzer Team  
Версия: 5.0.0  
Дата релиза: 2026-01-14

## 📞 Поддержка

Для вопросов и предложений создавайте [Issues](https://github.com/OlegKarenkikh/json2mermaid/issues) в репозитории.

## 🔗 Полезные ссылки

- [API Documentation](docs/API.md)
- [Changelog](docs/CHANGELOG.md)
- [Examples](examples/)
- [Mermaid Documentation](https://mermaid-js.github.io/)
- [GraphViz Documentation](https://graphviz.org/documentation/)

---

**Note**: Этот инструмент разработан для анализа диалоговых систем и может быть адаптирован для различных форматов данных.
