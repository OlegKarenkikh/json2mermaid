# utils/freshness_analyzer.py v5.1
"""Data freshness and update activity analysis"""

from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from collections import defaultdict

def convert_ticks_to_datetime(ticks: int) -> Optional[datetime]:
    """Convert .NET ticks to datetime"""
    if not ticks or ticks <= 0:
        return None
    
    try:
        TICKS_TO_UNIX_EPOCH = 621355968000000000
        TICKS_PER_SECOND = 10000000
        unix_seconds = (ticks - TICKS_TO_UNIX_EPOCH) / TICKS_PER_SECOND
        
        # Range validation to prevent OSError on Windows
        if unix_seconds < 0 or unix_seconds > 253402300799:
            return None
        
        return datetime.fromtimestamp(unix_seconds)
    except (ValueError, OverflowError, OSError):
        return None

def analyze_data_freshness(intents: List[Dict], reference_date: Optional[datetime] = None) -> Dict[str, Any]:
    """Analyze how fresh the data is (update activity)"""
    print("\n📅 Анализ свежести данных...")
    
    if reference_date is None:
        reference_date = datetime.now()
    
    version_dates = []
    skipped = 0
    
    for intent in intents:
        version = intent.get('version', 0)
        if version > 0:
            dt = convert_ticks_to_datetime(version)
            if dt:
                version_dates.append(dt)
            else:
                skipped += 1
    
    if not version_dates:
        print("   ⚠️  Нет данных о версиях")
        if skipped > 0:
            print(f"   (пропущено невалидных: {skipped})")
        return {
            'has_version_data': False,
            'message': 'No version data available',
            'skipped_invalid': skipped
        }
    
    if skipped > 0:
        print(f"   ⚠️  Пропущено невалидных timestamps: {skipped}")
    
    # Sort dates
    version_dates.sort()
    
    oldest = version_dates[0]
    newest = version_dates[-1]
    date_range = (newest - oldest).days
    
    # Count updates by period
    last_day = sum(1 for dt in version_dates if (reference_date - dt).days <= 1)
    last_week = sum(1 for dt in version_dates if (reference_date - dt).days <= 7)
    last_month = sum(1 for dt in version_dates if (reference_date - dt).days <= 30)
    
    total = len(version_dates)
    
    # Activity score (0-100)
    recent_ratio = last_month / total if total > 0 else 0
    activity_score = min(100, int(recent_ratio * 100))
    
    # Freshness category
    if activity_score >= 80:
        freshness = "very_fresh"
        freshness_emoji = "🟢"
    elif activity_score >= 60:
        freshness = "fresh"
        freshness_emoji = "🟡"
    elif activity_score >= 40:
        freshness = "moderate"
        freshness_emoji = "🟠"
    elif activity_score >= 20:
        freshness = "stale"
        freshness_emoji = "🟡"
    else:
        freshness = "very_stale"
        freshness_emoji = "🔴"
    
    # Print summary
    print(f"   Диапазон дат: {oldest.strftime('%Y-%m-%d')} - {newest.strftime('%Y-%m-%d')} ({date_range} дней)")
    print(f"   Обновлено за месяц: {last_month} ({round(recent_ratio*100, 1)}%)")
    print(f"   {freshness_emoji} Activity Score: {activity_score}/100 ({freshness})")
    
    return {
        'has_version_data': True,
        'oldest_date': oldest.isoformat(),
        'newest_date': newest.isoformat(),
        'date_range_days': date_range,
        'total_intents': total,
        'updated_last_day': last_day,
        'updated_last_week': last_week,
        'updated_last_month': last_month,
        'last_month_percentage': round(recent_ratio * 100, 1),
        'activity_score': activity_score,
        'freshness': freshness,
        'skipped_invalid': skipped
    }

def get_update_distribution(intents: List[Dict]) -> Dict[str, Any]:
    """Get distribution of updates over time"""
    updates_by_day = defaultdict(int)
    
    for intent in intents:
        version = intent.get('version', 0)
        if version > 0:
            dt = convert_ticks_to_datetime(version)
            if dt:
                day_key = dt.strftime('%Y-%m-%d')
                updates_by_day[day_key] += 1
    
    # Sort by date
    sorted_updates = sorted(updates_by_day.items())
    
    peak_day = max(updates_by_day.items(), key=lambda x: x[1]) if updates_by_day else None
    
    return {
        'updates_by_day': dict(sorted_updates),
        'peak_day': peak_day,
        'unique_days': len(updates_by_day)
    }
