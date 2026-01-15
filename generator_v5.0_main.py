#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Dialog Analyzer v5.1
Анализатор диалоговых потоков с полной валидацией и анализом графа
"""

import os
import sys

from utils.config import *
from utils.loaders import load_intents
from utils.validators import run_all_validations, save_validation_report
from utils.analyzers import first_pass, second_pass, third_pass, fourth_pass

# Import new graph analyzer
try:
    from utils.graph_analyzer import analyze_graph_structure
    GRAPH_ANALYSIS_AVAILABLE = True
except ImportError:
    GRAPH_ANALYSIS_AVAILABLE = False
    print("⚠️  Graph analysis module not available")

def print_section(title: str, width: int = 80):
    """Print formatted section header"""
    print("\n" + "="*width)
    print(title)
    print("="*width)

def main():
    """Main analyzer function"""
    print_section("🚀 DIALOG ANALYZER v5.1")
    print()
    
    # Check input file
    if not os.path.exists(INPUT_FILE):
        print(f"❌ Файл не найден: {INPUT_FILE}")
        print(f"💡 Создайте файл intent_data.jsonl с данными интентов")
        return 1
    
    # 1. Load data
    print_section("📅 ЭТАП 1: Загрузка данных")
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
    
    # 2. Validation
    if ENABLE_VALIDATION:
        print_section("🔍 ЭТАП 2: Валидация данных")
        validation_results = run_all_validations(intents, {})
        
        if STOP_ON_VALIDATION_ERRORS and not validation_results['summary']['is_valid']:
            print("\n❌ Остановка из-за ошибок валидации")
            return 1
        
        # Save validation report
        os.makedirs(OUTPUT_DIR, exist_ok=True)
        save_validation_report(validation_results, OUTPUT_DIR)
    
    # 3. Analysis (4 passes)
    print_section("🔬 ЭТАП 3: Анализ данных (4 прохода)")
    all_data = first_pass(intents)
    all_data = second_pass(intents, all_data)
    all_data = third_pass(intents, all_data)
    all_data = fourth_pass(intents, all_data)
    
    # 4. Graph structure analysis
    if GRAPH_ANALYSIS_AVAILABLE and ENABLE_VALIDATION:
        redirect_map = validation_results.get('redirects', {}).get('redirect_map', {})
        graph_analysis = analyze_graph_structure(intents, redirect_map)
        all_data['graph_analysis'] = graph_analysis
    
    # 5. Statistics
    print_section("📊 ЭТАП 4: Статистика")
    print(f"   Всего интентов: {len(intents)}")
    print(f"   Переходов: {len(all_data.get('transitions', []))}")
    
    # Count by types
    type_counts = {}
    for intent_id, classification in all_data['classifications'].items():
        intent_type = classification.intent_type
        type_counts[intent_type] = type_counts.get(intent_type, 0) + 1
    
    print(f"\n   Распределение по типам:")
    for intent_type, count in sorted(type_counts.items(), key=lambda x: -x[1]):
        print(f"      {intent_type}: {count}")
    
    # Count by subtypes
    if CLASSIFY_SUBTYPES:
        subtype_counts = {}
        for intent_id, classification in all_data['classifications'].items():
            if classification.subtype:
                subtype_counts[classification.subtype] = subtype_counts.get(classification.subtype, 0) + 1
        
        if subtype_counts:
            print(f"\n   Распределение по подтипам:")
            for subtype, count in sorted(subtype_counts.items(), key=lambda x: -x[1]):
                print(f"      {subtype}: {count}")
    
    # Final message
    print_section("✅ АНАЛИЗ ЗАВЕРШЁН УСПЕШНО!")
    print()
    print(f"📁 Результаты сохранены в: {OUTPUT_DIR}/")
    
    if ENABLE_VALIDATION:
        print(f"📄 Отчёт валидации: {OUTPUT_DIR}/validation_report.json")
        
        summary = validation_results.get('summary', {})
        if summary.get('error_count', 0) > 0:
            print(f"\n⚠️  Обнаружено ошибок: {summary['error_count']}")
            print("   Проверьте validation_report.json для деталей")
        
        if summary.get('has_warnings', False):
            print(f"💡 Предупреждений: {summary.get('warning_count', 0)}")
    
    print()
    print("💡 Используйте полученные данные для оптимизации диалоговых потоков")
    print()
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
