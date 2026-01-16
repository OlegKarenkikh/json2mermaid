#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Dialog Analyzer v5.3 ROBUST PARSING + COMPREHENSIVE TRANSITIONS
Анализатор диалоговых потоков с надёжным парсингом невалидного JSONL
"""

import os
import sys
import json

# Добавляем текущую директорию в путь для импорта utils
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from utils.config import *
from utils.loaders import load_intents
from utils.validators import run_all_validations, save_validation_report
from utils.analyzers import first_pass, second_pass, third_pass, fourth_pass

# Import graph analyzer
try:
    from utils.graph_analyzer import analyze_graph_structure
    GRAPH_ANALYSIS_AVAILABLE = True
except ImportError:
    GRAPH_ANALYSIS_AVAILABLE = False
    print("⚠️  Graph analysis module not available")

# Import risk analyzer
try:
    from utils.risk_analyzer import (
        analyze_intent_risks, generate_risk_summary,
        generate_risk_legend, export_risk_report
    )
    RISK_ANALYSIS_AVAILABLE = True
except ImportError:
    RISK_ANALYSIS_AVAILABLE = False
    print("⚠️  Risk analysis module not available")

# Import quality analyzers
try:
    from utils.regex_analyzer import analyze_intent_regex_patterns
    REGEX_ANALYSIS_AVAILABLE = True
except ImportError:
    REGEX_ANALYSIS_AVAILABLE = False
    print("⚠️  Regex analysis module not available")

try:
    from utils.entry_point_analyzer import analyze_entry_points
    ENTRY_POINT_ANALYSIS_AVAILABLE = True
except ImportError:
    ENTRY_POINT_ANALYSIS_AVAILABLE = False
    print("⚠️  Entry point analysis module not available")

try:
    from utils.freshness_analyzer import analyze_data_freshness, get_update_distribution
    FRESHNESS_ANALYSIS_AVAILABLE = True
except ImportError:
    FRESHNESS_ANALYSIS_AVAILABLE = False
    print("⚠️  Freshness analysis module not available")

try:
    from utils.diagram_exporter import export_mermaid_graph, export_detailed_flow_diagram
    DIAGRAM_EXPORT_AVAILABLE = True
except ImportError:
    DIAGRAM_EXPORT_AVAILABLE = False
    print("⚠️  Diagram export module not available")

try:
    from utils.multi_format_exporter import export_all_formats
    MULTI_FORMAT_EXPORT_AVAILABLE = True
except ImportError:
    MULTI_FORMAT_EXPORT_AVAILABLE = False
    print("⚠️  Multi-format export module not available")

def print_header():
    """Печать красивого заголовка"""
    print()
    print("=" * 80)
    print("🚀 DIALOG ANALYZER v5.3 - COMPREHENSIVE TRANSITIONS")
    print("=" * 80)
    print("📜 Режим: Read-Only Analysis with Robust JSONL Parsing")
    print("🛡️  Данные не изменяются - только визуализация и метрики")
    print("🔧 НОВОЕ: Обработка невалидного JSONL (Extra data, multiple objects)")
    print("📊 ВКЛЮЧЕНО: Риски, граф, метрики качества, все типы переходов")
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
    validation_results = {}
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
    
    # Получаем полные объекты Transition
    transitions_full = all_data.get('transitions', [])
    # Для graph_analyzer нужны кортежи
    transitions_tuples = [(t.source_id, t.target_id) for t in transitions_full]

    # 4. Анализ графа
    if GRAPH_ANALYSIS_AVAILABLE and ENABLE_VALIDATION:
        redirect_map = validation_results.get('redirects', {}).get('redirect_map', {})
        graph_analysis = analyze_graph_structure(intents, redirect_map, transitions_tuples)
        all_data['graph_analysis'] = graph_analysis
        validation_results['graph_analysis'] = graph_analysis

    # 5. Метрики качества
    quality_metrics = {}
    print()
    print("=" * 80)
    print("📊 ЭТАП 4: Анализ качества данных")
    print("=" * 80)

    if REGEX_ANALYSIS_AVAILABLE:
        regex_analysis = analyze_intent_regex_patterns(intents)
        quality_metrics['regex_complexity'] = regex_analysis

    if ENTRY_POINT_ANALYSIS_AVAILABLE:
        entry_point_analysis = analyze_entry_points(intents)
        quality_metrics['entry_points'] = entry_point_analysis

    if FRESHNESS_ANALYSIS_AVAILABLE:
        freshness_analysis = analyze_data_freshness(intents)
        if freshness_analysis.get('has_version_data'):
            update_dist = get_update_distribution(intents)
            freshness_analysis['update_distribution'] = update_dist
        quality_metrics['data_freshness'] = freshness_analysis

    # 6. Анализ рисков
    if RISK_ANALYSIS_AVAILABLE and ENABLE_VALIDATION:
        print()
        print("=" * 80)
        print("🛡️  ЭТАП 5: Анализ рисков")
        print("=" * 80)

        intent_risks = analyze_intent_risks(intents, validation_results)
        risk_summary = generate_risk_summary(intent_risks)

        risk_score = risk_summary['risk_score']
        if risk_score >= 80:
            score_icon = "✅"
        elif risk_score >= 60:
            score_icon = "🟡"
        elif risk_score >= 40:
            score_icon = "🟠"
        else:
            score_icon = "🔴"

        print(f"\n{score_icon} Общий рейтинг рисков: {risk_score}/100")

        print(f"\n📊 Распределение по уровням риска:")
        severity_dist = risk_summary['severity_distribution']
        for severity in ['critical', 'high', 'medium', 'low', 'info']:
            count = severity_dist.get(severity, 0)
            if count > 0:
                pct = round(count / risk_summary['total_intents'] * 100, 1)
                print(f"   {severity.upper():10s}: {count:4d} ({pct}%)")

        critical_intents = risk_summary['critical_intents']
        if critical_intents:
            print(f"\n❌ КРИТИЧЕСКИЕ ИНТЕНТЫ ({len(critical_intents)}):")
            for intent_id in critical_intents[:5]:
                risk_obj = intent_risks[intent_id]
                print(f"   - {intent_id}")
                for _, desc in risk_obj.risks[:2]:
                    print(f"      • {desc}")
            if len(critical_intents) > 5:
                print(f"   ... и ещё {len(critical_intents) - 5}")

        print(generate_risk_legend())

        risk_report_path = os.path.join(OUTPUT_DIR, 'risk_analysis.json')
        export_risk_report(intent_risks, risk_report_path)

        if quality_metrics:
            with open(risk_report_path, 'r', encoding='utf-8') as f:
                report = json.load(f)
            report['quality_metrics'] = quality_metrics
            with open(risk_report_path, 'w', encoding='utf-8') as f:
                json.dump(report, f, indent=2, ensure_ascii=False)
            print(f"\n📊 Метрики качества добавлены в отчёт")

        all_data['intent_risks'] = intent_risks
        all_data['quality_metrics'] = quality_metrics

    # 6.1 Diagram export - Передаём полные объекты Transition
    if EXPORT_DIAGRAMS and DIAGRAM_EXPORT_AVAILABLE:
        print()
        print("=" * 80)
        print("🖌️  ЭТАП 6: Генерация диаграмм")
        print("=" * 80)
        
        # Mermaid диаграммы (для небольших графов)
        if len(intents) <= 1000:
            # Стандартная диаграмма графа
            diagram_path = os.path.join(OUTPUT_DIR, "graph.mmd")
            export_mermaid_graph(
                intents=intents,
                transitions=transitions_full,  # Полные объекты!
                intent_risks=all_data.get('intent_risks'),
                output_path=diagram_path,
                include_legend=INCLUDE_LEGEND,
            )
            print(f"\n🖌️  Mermaid диаграмма сохранена: {diagram_path}")
            
            # Детальная диаграмма с полной логикой обработки
            detailed_diagram_path = os.path.join(OUTPUT_DIR, "detailed_flow.mmd")
            export_detailed_flow_diagram(
                intents=intents,
                output_path=detailed_diagram_path,
                show_slot_conditions=True,
                show_buttons=True,
                show_regex=True,
            )
            print(f"🖌️  Детальная Mermaid диаграмма: {detailed_diagram_path}")
            print(f"👁️  Просмотр Mermaid: https://mermaid.live/")
        else:
            print(f"\n⚠️  Mermaid пропущен ({len(intents)} интентов > 1000 лимит)")
        
        # Мульти-форматный экспорт (для больших графов)
        if MULTI_FORMAT_EXPORT_AVAILABLE:
            print()
            export_all_formats(
                intents=intents,
                transitions=transitions_full,
                output_dir=OUTPUT_DIR,
                base_name="dialog_flow",
                render_images=True,  # Попытаться создать SVG/PNG если Graphviz установлен
            )
        else:
            print("\n⚠️  Мульти-форматный экспорт недоступен")
    
    # 7. Статистика
    print()
    print("=" * 80)
    print("📊 ЭТАП 7: Итоговая статистика")
    print("=" * 80)
    print(f"📦 Всего интентов: {len(intents)}")
    print(f"🔗 Переходов: {len(transitions_full)}")
    
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
    if RISK_ANALYSIS_AVAILABLE:
        print(f"📄 Отчёт рисков: {OUTPUT_DIR}/risk_analysis.json")
    if EXPORT_DIAGRAMS:
        print(f"🖌️  Диаграммы:")
        if len(intents) <= 1000:
            print(f"   • Mermaid: {OUTPUT_DIR}/graph.mmd, detailed_flow.mmd")
        print(f"   • Graphviz: {OUTPUT_DIR}/dialog_flow.dot (.svg)")
        print(f"   • GraphML (yEd): {OUTPUT_DIR}/dialog_flow.graphml")
        print(f"   • GEXF (Gephi): {OUTPUT_DIR}/dialog_flow.gexf")
        print(f"   • JSON (web): {OUTPUT_DIR}/dialog_flow_*.json")
    print()
    print("💡 Рекомендации по просмотру больших диаграмм:")
    print("   • Gephi (https://gephi.org/) - лучший для 1000+ узлов")
    print("   • yEd (https://www.yworks.com/yed) - хорош для GraphML")
    print("   • Cytoscape (https://cytoscape.org/) - интерактивный анализ")
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
