#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Dialog Analyzer v5.0 FINAL
Анализатор диалоговых потоков с полной валидацией
"""

import os
import sys

from utils.config import *
from utils.loaders import load_intents
from utils.validators import run_all_validations, save_validation_report
from utils.analyzers import first_pass, second_pass, third_pass, fourth_pass

def main():
    """Главная функция анализатора"""
    print("=" * 80)
    print("🚀 DIALOG ANALYZER v5.0 FINAL")
    print("=" * 80)
    print()

    # Проверка входного файла
    if not os.path.exists(INPUT_FILE):
        print(f"❌ Файл не найден: {INPUT_FILE}")
        print(f"💡 Создайте файл intent_data.jsonl с данными интентов")
        return 1

    # 1. Загрузка данных
    print("📥 ЭТАП 1: Загрузка данных")
    print("-" * 80)
    intents, metadata = load_intents(INPUT_FILE, MAX_LINES)
    
    if not intents:
        print("❌ Нет данных для анализа")
        return 1

    print(f"\n📊 Метаданные:")
    print(f"   Всего загружено: {metadata.get('total_loaded', 0)}")
    print(f"   Финальное количество: {metadata.get('final_count', 0)}")
    
    if 'filtered_expired' in metadata:
        print(f"   Отфильтровано истёкших: {metadata['filtered_expired']}")

    version_stats = metadata.get('version_statistics', {})
    if version_stats:
        print(f"\n📈 Статистика версий:")
        print(f"   С версией: {version_stats.get('with_version', 0)}")
        print(f"   С expire: {version_stats.get('with_expire', 0)}")
        print(f"   Активных: {version_stats.get('active', 0)}")
        print(f"   Истёкших: {version_stats.get('expired', 0)}")

    # 2. Валидация
    if ENABLE_VALIDATION:
        print("\n🔍 ЭТАП 2: Валидация данных")
        print("-" * 80)
        validation_results = run_all_validations(intents, {})
        
        if STOP_ON_VALIDATION_ERRORS and not validation_results['summary']['is_valid']:
            print("\n❌ Остановка из-за ошибок валидации")
            return 1

        # Сохранение отчёта валидации
        os.makedirs(OUTPUT_DIR, exist_ok=True)
        save_validation_report(validation_results, OUTPUT_DIR)

    # 3. Анализ (4 прохода)
    print("\n🔬 ЭТАП 3: Анализ данных (4 прохода)")
    print("-" * 80)

    all_data = first_pass(intents)
    all_data = second_pass(intents, all_data)
    all_data = third_pass(intents, all_data)
    all_data = fourth_pass(intents, all_data)

    # 4. Статистика
    print("\n📊 ЭТАП 4: Статистика")
    print("-" * 80)
    print(f"   Всего интентов: {len(intents)}")
    print(f"   Переходов: {len(all_data.get('transitions', []))}")

    # Подсчёт по типам
    type_counts = {}
    for intent_id, classification in all_data['classifications'].items():
        intent_type = classification.intent_type
        type_counts[intent_type] = type_counts.get(intent_type, 0) + 1

    print(f"\n   Распределение по типам:")
    for intent_type, count in sorted(type_counts.items(), key=lambda x: -x[1]):
        print(f"     {intent_type}: {count}")

    # Подсчёт по подтипам
    if CLASSIFY_SUBTYPES:
        subtype_counts = {}
        for intent_id, classification in all_data['classifications'].items():
            if classification.subtype:
                subtype_counts[classification.subtype] = subtype_counts.get(classification.subtype, 0) + 1
        
        if subtype_counts:
            print(f"\n   Распределение по подтипам:")
            for subtype, count in sorted(subtype_counts.items(), key=lambda x: -x[1]):
                print(f"     {subtype}: {count}")

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
    sys.exit(main())
