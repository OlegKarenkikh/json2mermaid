#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Dialog Analyzer v5.1 ROBUST PARSING
Анализатор диалоговых потоков с надёжным парсингом невалидного JSONL
"""

import os
import sys

# Добавляем текущую директорию в путь для импорта utils
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from utils.config import *
from utils.loaders import load_intents
from utils.validators import run_all_validations, save_validation_report
from utils.analyzers import first_pass, second_pass, third_pass, fourth_pass

def print_header():
    """Печать красивого заголовка"""
    print()
    print("=" * 80)
    print("🚀 DIALOG ANALYZER v5.1 - ROBUST PARSING EDITION")
    print("=" * 80)
    print("📜 Режим: Read-Only Analysis with Robust JSONL Parsing")
    print("🛡️  Данные не изменяются - только визуализация и метрики")
    print("🔧 НОВОЕ: Обработка невалидного JSONL (Extra data, multiple objects)")
    print()

def main():
    """Главная функция анализатора"""
    print_header()
    
    # Проверка входного файла
    print("=" * 80)
    print("📅 ЭТАП 1: Загрузка данных")
    print("=" * 80)
    
    if not os.path.exists(INPUT_FILE):
        print(f"❌ Файл не найден: {INPUT_FILE}")
        print(f"💡 Создайте файл {INPUT_FILE} или укажите путь в utils/config.py")
        print()
        print("📝 Ожидаемый формат: JSONL (по одному JSON на строку)")
        print("   Пример:")
        print('   {"intent_id": "1", "title": "Test", ...}')
        print('   {"intent_id": "2", "title": "Test 2", ...}')
        return 1
    
    # 1. Загрузка данных
    intents, metadata = load_intents(INPUT_FILE, MAX_LINES)
    
    if not intents:
        print()
        print("=" * 80)
        print("❌ Нет данных для анализа")
        print("=" * 80)
        print()
        print("📝 Возможные причины:")
        print("   1. Файл пустой")
        print("   2. Все строки имеют невалидный JSON")
        print("   3. Файл не в формате JSON/JSONL")
        print()
        print("💡 Проверьте первые строки файла:")
        try:
            with open(INPUT_FILE, 'r', encoding='utf-8') as f:
                for i, line in enumerate(f):
                    if i >= 3:
                        break
                    print(f"   Line {i+1}: {line[:80]}...")
        except Exception as e:
            print(f"   Ошибка чтения: {e}")
        print()
        return 1
    
    # Статистика загрузки
    print()
    print("=" * 80)
    print("📊 Статистика загрузки")
    print("=" * 80)
    print(f"✅ Всего загружено: {metadata.get('total_loaded', 0)} интентов")
    print(f"📝 Обработано строк: {metadata.get('total_lines_processed', 0)}")
    
    parsing_stats = metadata.get('parsing_stats', {})
    if parsing_stats:
        print()
        print("🔍 Детали парсинга:")
        print(f"   ✅ Успешно: {parsing_stats.get('success', 0)}")
        if parsing_stats.get('fixed_extra_data', 0) > 0:
            print(f"   🔧 Исправлено (Extra data): {parsing_stats['fixed_extra_data']}")
        if parsing_stats.get('skipped_empty', 0) > 0:
            print(f"   ⚪ Пропущено (пустые): {parsing_stats['skipped_empty']}")
        if parsing_stats.get('skipped_invalid', 0) > 0:
            print(f"   ⚠️  Пропущено (невалидный JSON): {parsing_stats['skipped_invalid']}")
    
    if 'filtered_expired' in metadata:
        print(f"   🗑️  Отфильтровано истёкших: {metadata['filtered_expired']}")
    
    print(f"   📦 Финальное количество: {metadata.get('final_count', 0)}")
    
    version_stats = metadata.get('version_statistics', {})
    if version_stats and any(version_stats.values()):
        print()
        print("📈 Статистика версий:")
        print(f"   С версией: {version_stats.get('with_version', 0)}")
        print(f"   С expire: {version_stats.get('with_expire', 0)}")
        print(f"   Активных: {version_stats.get('active', 0)}")
        print(f"   Истёкших: {version_stats.get('expired', 0)}")
    
    # 2. Валидация
    if ENABLE_VALIDATION:
        print()
        print("=" * 80)
        print("🔍 ЭТАП 2: Валидация данных")
        print("=" * 80)
        validation_results = run_all_validations(intents, {})
        
        if STOP_ON_VALIDATION_ERRORS and not validation_results['summary']['is_valid']:
            print()
            print("❌ Остановка из-за критических ошибок валидации")
            print("💡 Отключите STOP_ON_VALIDATION_ERRORS в config.py для продолжения")
            return 1
        
        # Сохранение отчёта валидации
        os.makedirs(OUTPUT_DIR, exist_ok=True)
        save_validation_report(validation_results, OUTPUT_DIR)
        print(f"📄 Отчёт валидации: {OUTPUT_DIR}/validation_report.json")
    
    # 3. Анализ (4 прохода)
    print()
    print("=" * 80)
    print("🔬 ЭТАП 3: Анализ данных (4 прохода)")
    print("=" * 80)
    
    all_data = first_pass(intents)
    all_data = second_pass(intents, all_data)
    all_data = third_pass(intents, all_data)
    all_data = fourth_pass(intents, all_data)
    
    # 4. Статистика
    print()
    print("=" * 80)
    print("📊 ЭТАП 4: Итоговая статистика")
    print("=" * 80)
    print(f"📦 Всего интентов: {len(intents)}")
    print(f"🔗 Переходов: {len(all_data.get('transitions', []))}")
    
    # Подсчёт по типам
    type_counts = {}
    for intent_id, classification in all_data.get('classifications', {}).items():
        intent_type = classification.intent_type
        type_counts[intent_type] = type_counts.get(intent_type, 0) + 1
    
    if type_counts:
        print()
        print("📋 Распределение по типам:")
        for intent_type, count in sorted(type_counts.items(), key=lambda x: -x[1]):
            percentage = (count / len(intents)) * 100
            print(f"   {intent_type}: {count} ({percentage:.1f}%)")
    
    # Подсчёт по подтипам
    if CLASSIFY_SUBTYPES:
        subtype_counts = {}
        for intent_id, classification in all_data.get('classifications', {}).items():
            if classification.subtype:
                subtype_counts[classification.subtype] = subtype_counts.get(classification.subtype, 0) + 1
        
        if subtype_counts:
            print()
            print("🏷️  Распределение по подтипам:")
            for subtype, count in sorted(subtype_counts.items(), key=lambda x: -x[1])[:10]:
                percentage = (count / len(intents)) * 100
                print(f"   {subtype}: {count} ({percentage:.1f}%)")
    
    # Финальное сообщение
    print()
    print("=" * 80)
    print("✅ АНАЛИЗ ЗАВЕРШЁН УСПЕШНО!")
    print("=" * 80)
    print()
    print(f"📁 Результаты сохранены в: {OUTPUT_DIR}/")
    if ENABLE_VALIDATION:
        print(f"📄 Отчёт валидации: {OUTPUT_DIR}/validation_report.json")
    print()
    print("💡 Используйте полученные данные для оптимизации диалоговых потоков")
    print()
    
    return 0

if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print()
        print()
        print("⚠️  Прервано пользователем")
        sys.exit(1)
    except Exception as e:
        print()
        print()
        print("=" * 80)
        print("❌ КРИТИЧЕСКАЯ ОШИБКА")
        print("=" * 80)
        print(f"Тип: {type(e).__name__}")
        print(f"Сообщение: {e}")
        print()
        import traceback
        traceback.print_exc()
        print()
        sys.exit(1)
