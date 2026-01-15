# Dialog Analyzer v5.0 - API Documentation

## Модули

### utils.loaders

#### load_intents(filepath, max_lines=None)
Загружает интенты из JSON/JSONL файла

**Параметры:**
- `filepath` (str): Путь к файлу
- `max_lines` (int, optional): Максимальное количество строк

**Возвращает:**
- tuple: (список интентов, метаданные)

**Пример:**
```python
from utils.loaders import load_intents

intents, metadata = load_intents("intent_data.jsonl")
print(f"Загружено: {len(intents)}")
```

### utils.validators

#### run_all_validations(intents, all_data)
Запускает все проверки валидации

**Параметры:**
- `intents` (List[Dict]): Список интентов
- `all_data` (Dict): Данные анализа

**Возвращает:**
- Dict: Результаты валидации

**Пример:**
```python
from utils.validators import run_all_validations

results = run_all_validations(intents, {})
if results['summary']['is_valid']:
    print("✅ Все проверки пройдены")
```

### utils.analyzers

#### first_pass(intents)
Первый проход: сбор базовых данных

#### second_pass(intents, all_data)
Второй проход: NER анализ

#### third_pass(intents, all_data)
Третий проход: анализ связей

#### fourth_pass(intents, all_data)
Четвёртый проход: финальный анализ

**Пример:**
```python
from utils.analyzers import first_pass, second_pass

all_data = first_pass(intents)
all_data = second_pass(intents, all_data)
```

### utils.version_manager

#### filter_expired_intents(intents)
Фильтрует истёкшие интенты

**Возвращает:**
- tuple: (активные интенты, количество истёкших)

#### get_version_statistics(intents)
Собирает статистику по версиям

**Возвращает:**
- Dict: Статистика версий
