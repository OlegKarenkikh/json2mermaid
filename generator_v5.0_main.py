#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Dialog Analyzer v5.1 - Risk-Aware + Quality Metrics Edition
Анализатор диалоговых потоков с визуализацией рисков и метриками качества

Принципы:
- Читаем данные "как есть" (без изменений)
- Визуализируем все проблемы цветом
- Подсвечиваем риски, но не исправляем
- Сохраняем audit trail для ручного review
- Измеряем качество продукционных данных
"""

import os
import sys
import json

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

# Import quality analyzers (NEW!)
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
    from utils.diagram_exporter import export_mermaid_graph
    DIAGRAM_EXPORT_AVAILABLE = True
except ImportError:
    DIAGRAM_EXPORT_AVAILABLE = False
    print("⚠️  Diagram export module not available")

def print_section(title: str, width: int = 80):
    """Print formatted section header"""
    print("\n" + "="*width)
    print(title)
    print("="*width)

def main():
    """Main analyzer function"""
    print_section("🚀 DIALOG ANALYZER v5.1 - QUALITY METRICS EDITION")
    print("📜 Режим: Read-Only Analysis with Quality Metrics")
    print("🛡️  Данные не изменяются - только визуализация и метрики")
    print("📊 НОВОЕ: Анализ качества production-ready данных")
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
    validation_results = {}
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
    transitions = [(t.source_id, t.target_id) for t in all_data.get('transitions', [])]
    
    # 4. Graph structure analysis
    if GRAPH_ANALYSIS_AVAILABLE and ENABLE_VALIDATION:
        redirect_map = validation_results.get('redirects', {}).get('redirect_map', {})
        graph_analysis = analyze_graph_structure(intents, redirect_map, transitions)
        all_data['graph_analysis'] = graph_analysis
        validation_results['graph_analysis'] = graph_analysis
    
    # 5. Quality Metrics Analysis (NEW!)
    quality_metrics = {}
    print_section("📊 ЭТАП 4: Анализ качества данных")
    
    # 5.1 Regex complexity
    if REGEX_ANALYSIS_AVAILABLE:
        regex_analysis = analyze_intent_regex_patterns(intents)
        quality_metrics['regex_complexity'] = regex_analysis
    
    # 5.2 Entry point diversity
    if ENTRY_POINT_ANALYSIS_AVAILABLE:
        entry_point_analysis = analyze_entry_points(intents)
        quality_metrics['entry_points'] = entry_point_analysis
    
    # 5.3 Data freshness
    if FRESHNESS_ANALYSIS_AVAILABLE:
        freshness_analysis = analyze_data_freshness(intents)
        if freshness_analysis['has_version_data']:
            update_dist = get_update_distribution(intents)
            freshness_analysis['update_distribution'] = update_dist
        quality_metrics['data_freshness'] = freshness_analysis
    
    # 6. Risk Analysis
    if RISK_ANALYSIS_AVAILABLE and ENABLE_VALIDATION:
        print_section("🛡️  ЭТАП 5: Анализ рисков")
        
        # Analyze risks
        intent_risks = analyze_intent_risks(intents, validation_results)
        risk_summary = generate_risk_summary(intent_risks)
        
        # Display risk score
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
        
        # Display severity distribution
        print(f"\n📊 Распределение по уровням риска:")
        severity_dist = risk_summary['severity_distribution']
        for severity in ['critical', 'high', 'medium', 'low', 'info']:
            count = severity_dist.get(severity, 0)
            if count > 0:
                pct = round(count / risk_summary['total_intents'] * 100, 1)
                print(f"   {severity.upper():10s}: {count:4d} ({pct}%)")
        
        # Show critical intents
        critical_intents = risk_summary['critical_intents']
        if critical_intents:
            print(f"\n❌ КРИТИЧЕСКИЕ ИНТЕНТЫ ({len(critical_intents)}):")
            for intent_id in critical_intents[:5]:
                risk_obj = intent_risks[intent_id]
                print(f"   - {intent_id}")
                for risk_type, desc in risk_obj.risks[:2]:
                    print(f"      • {desc}")
            if len(critical_intents) > 5:
                print(f"   ... и ещё {len(critical_intents) - 5}")
        
        # Display risk legend
        print(generate_risk_legend())
        
        # Export comprehensive report with quality metrics
        risk_report_path = os.path.join(OUTPUT_DIR, 'risk_analysis.json')
        export_risk_report(intent_risks, risk_report_path)
        
        # Add quality metrics to report
        if quality_metrics:
            with open(risk_report_path, 'r', encoding='utf-8') as f:
                report = json.load(f)
            report['quality_metrics'] = quality_metrics
            with open(risk_report_path, 'w', encoding='utf-8') as f:
                json.dump(report, f, indent=2, ensure_ascii=False)
            print(f"\n📊 Метрики качества добавлены в отчёт")
        
        # Store in all_data for diagram generation
        all_data['intent_risks'] = intent_risks
        all_data['quality_metrics'] = quality_metrics

    # 6.1 Diagram export (Mermaid)
    if EXPORT_DIAGRAMS and DIAGRAM_EXPORT_AVAILABLE:
        diagram_path = os.path.join(OUTPUT_DIR, "graph.mmd")
        export_mermaid_graph(
            intents=intents,
            transitions=transitions,
            intent_risks=all_data.get('intent_risks'),
            output_path=diagram_path,
            include_legend=INCLUDE_LEGEND,
        )
        print(f"\n🖼️  Диаграмма Mermaid сохранена: {diagram_path}")
    
    # 7. Statistics
    print_section("📊 ЭТАП 6: Статистика")
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
    print(f"   • validation_report.json - полный отчёт валидации")
    
    if RISK_ANALYSIS_AVAILABLE:
        print(f"   • risk_analysis.json - анализ рисков + метрики качества")
    
    if ENABLE_VALIDATION:
        summary = validation_results.get('summary', {})
        if summary.get('error_count', 0) > 0:
            print(f"\n⚠️  Обнаружено ошибок: {summary['error_count']}")
            print("   👉 Проверьте validation_report.json для деталей")
        
        if summary.get('has_warnings', False):
            print(f"💡 Предупреждений: {summary.get('warning_count', 0)}")
    
    print()
    print("🔍 ВАЖНО: Исходные данные НЕ БЫЛИ ИЗМЕНЕНЫ")
    print("🎨 Проблемные узлы будут подсвечены на диаграммах")
    print("📊 Используйте risk_analysis.json для ручного review")
    print("✨ Метрики качества доступны в том же отчёте")
    print()
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
