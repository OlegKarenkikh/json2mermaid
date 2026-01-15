# Quality Metrics Guide v5.1

Руководство по метрикам качества production-ready данных

---

## 🎯 Обзор

Dialog Analyzer v5.1 включает **новые метрики** для оценки качества чистых, production-ready данных:

1. **Regex Complexity** - сложность регулярных выражений
2. **Entry Point Diversity** - разнообразие точек входа
3. **Data Freshness** - свежесть данных

Эти метрики **не обнаруживают ошибки**, а оценивают **поддерживаемость** и **активность** разработки.

---

## 1️⃣ Regex Complexity Analysis

### 🎯 Цель
Обнаружить **сложные regex паттерны**, которые:
- Трудно понять
- Трудно поддерживать
- Могут работать медленно

### 📊 Критерии

| Уровень | Длина | Альтернативы | Риск |
|---------|--------|------------------|------|
| **SIMPLE** | < 30 chars | 0-2 | 🟢 INFO |
| **MODERATE** | 30-100 chars | 3-5 | 🟡 LOW |
| **COMPLEX** | 100-200 chars | 6-10 | 🟠 MEDIUM |
| **VERY_COMPLEX** | > 200 chars | > 10 | 🔴 HIGH |

### 📝 Пример вывода

```
🔍 Анализ сложности regex паттернов...
   Всего паттернов: 1250
   Сложных (>100 символов): 45 (3.6%)

   ТОП-3 самых сложных:
   1. intent_osago_renew - 245 символов, 12 альтернатив
   2. intent_dms_purchase - 198 символов, 8 альтернатив
   3. intent_kasko_info - 156 символов, 10 альтернатив
```

### 📊 JSON формат

```json
{
  "regex_complexity": {
    "total_patterns": 1250,
    "complexity_distribution": {
      "simple": 800,
      "moderate": 380,
      "complex": 60,
      "very_complex": 10
    },
    "complex_count": 70,
    "complex_percentage": 5.6,
    "top_complex_patterns": [
      {
        "intent_id": "intent_osago_renew",
        "pattern": "(продлить|продление|продли|обновить...)...",
        "length": 245,
        "alternatives": 12,
        "issues": [
          "Too many alternatives (12)",
          "Many character classes (8)"
        ],
        "score": 385
      }
    ]
  }
}
```

### 💡 Рекомендации

**Если > 5% сложных паттернов:**
1. Разбейте на несколько интентов
2. Используйте NLU вместо regex
3. Добавьте комментарии к паттернам

---

## 2️⃣ Entry Point Diversity

### 🎯 Цель
Оценить **разнообразие каналов** входа в диалог:
- Основной (cc_regexp_main)
- Match-based (cc_match)
- Мессенджеры (Telegram/Viber)
- Системные
- Fallback

### 📊 Скоринг

| Типов | Diversity Score | Оценка |
|-------|----------------|--------|
| 1 | 25 | 🔴 Низкая |
| 2 | 50 | 🟡 Средняя |
| 3 | 75 | 🟢 Хорошая |
| 4+ | 100 | 🟢 Отличная |

### 📝 Пример вывода

```
🚪 Анализ точек входа...
   Всего точек входа: 45
   Уникальных типов: 3
   Diversity Score: 75/100

   Распределение:
      cc_regexp_main: 30
      cc_match: 10
      cc_viber_telegram: 5
```

### 📊 JSON формат

```json
{
  "entry_points": {
    "total_entry_points": 45,
    "type_distribution": {
      "cc_regexp_main": 30,
      "cc_match": 10,
      "cc_viber_telegram": 5
    },
    "unique_types": 3,
    "diversity_score": 75,
    "has_multiple_channels": true,
    "entry_points": [
      {
        "intent_id": "main_greeting",
        "type": "cc_regexp_main",
        "record_type": "cc_regexp_main",
        "title": "Приветствие"
      }
    ]
  }
}
```

### 💡 Рекомендации

**Если Diversity Score < 50:**
- Добавьте поддержку мессенджеров
- Разделите логику match vs regexp
- Добавьте fallback обработчики

---

## 3️⃣ Data Freshness

### 🎯 Цель
Оценить **активность разработки** по датам обновлений:
- Как давно обновлялся датасет?
- Сколько % обновлено за последний месяц?
- Есть ли активная разработка?

### 📊 Категории

| Activity Score | Категория | Оценка |
|----------------|-----------|--------|
| 80-100 | very_fresh | 🟢 Активная разработка |
| 60-79 | fresh | 🟡 Регулярные обновления |
| 40-59 | moderate | 🟠 Периодические |
| 20-39 | stale | 🔴 Устаревшие |
| 0-19 | very_stale | 🔴 Очень старые |

### 📝 Пример вывода

```
📅 Анализ свежести данных...
   Диапазон дат: 2025-08-19 - 2025-08-27 (8 дней)
   Обновлено за месяц: 1000 (80.0%)
   🟢 Activity Score: 80/100 (very_fresh)
```

### 📊 JSON формат

```json
{
  "data_freshness": {
    "has_version_data": true,
    "oldest_date": "2025-08-19T10:30:00",
    "newest_date": "2025-08-27T15:45:00",
    "date_range_days": 8,
    "total_intents": 1250,
    "updated_last_day": 50,
    "updated_last_week": 450,
    "updated_last_month": 1000,
    "last_month_percentage": 80.0,
    "activity_score": 80,
    "freshness": "very_fresh",
    "update_distribution": {
      "updates_by_day": {
        "2025-08-19": 120,
        "2025-08-20": 200,
        "2025-08-21": 180,
        "2025-08-27": 50
      },
      "peak_day": ["2025-08-20", 200],
      "unique_days": 8
    }
  }
}
```

### 💡 Рекомендации

**Если Activity Score < 40:**
- Проверьте актуальность датасета
- Обновите старые интенты
- Удалите неиспользуемые

---

## 📊 Объединённый отчёт

Все метрики сохраняются в `risk_analysis.json`:

```json
{
  "report_timestamp": "2026-01-15T18:15:00",
  "version": "5.1",
  "summary": {
    "risk_score": 85,
    "total_intents": 1250
  },
  "quality_metrics": {
    "regex_complexity": { ... },
    "entry_points": { ... },
    "data_freshness": { ... }
  },
  "intents": { ... }
}
```

---

## 🛠️ Использование

### Запуск анализа
```bash
python generator_v5.0_main.py
```

### Просмотр метрик
```bash
cat dialog_flow_analysis/risk_analysis.json | jq '.quality_metrics'
```

### Python API
```python
from utils.regex_analyzer import analyze_intent_regex_patterns
from utils.entry_point_analyzer import analyze_entry_points
from utils.freshness_analyzer import analyze_data_freshness

# Load intents
intents = load_intents('intent_data.jsonl')

# Run analysis
regex_metrics = analyze_intent_regex_patterns(intents)
entry_metrics = analyze_entry_points(intents)
freshness_metrics = analyze_data_freshness(intents)

# Get scores
print(f"Complex regex: {regex_metrics['complex_percentage']}%")
print(f"Diversity: {entry_metrics['diversity_score']}/100")
print(f"Freshness: {freshness_metrics['activity_score']}/100")
```

---

## 🎯 Общий Quality Score

Можно вычислить **общий скор**:

```python
quality_score = (
    (100 - regex_metrics['complex_percentage']) * 0.3 +  # 30%
    entry_metrics['diversity_score'] * 0.3 +              # 30%
    freshness_metrics['activity_score'] * 0.4             # 40%
)

if quality_score >= 80:
    print("🟢 Отличное качество")
elif quality_score >= 60:
    print("🟡 Хорошее качество")
else:
    print("🔴 Требуется улучшение")
```

---

## 📚 Дополнительно

- [CHANGELOG.md](CHANGELOG.md) - история изменений
- [README.md](../README.md) - основная документация
- [RISK_LEGEND.md](RISK_LEGEND.md) - легенда рисков

---

**Версия:** 5.1  
**Дата:** 2026-01-15  
**Автор:** Dialog Analyzer Team
