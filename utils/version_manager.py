# utils/version_manager.py
from typing import List, Dict, Any, Tuple
from datetime import datetime

def filter_expired_intents(intents: List[Dict[str, Any]]) -> Tuple[List[Dict[str, Any]], int]:
    """
    Фильтрует истёкшие интенты (с expire_at в прошлом)
    
    Args:
        intents: Список интентов
    
    Returns:
        Tuple[активные интенты, количество истёкших]
    """
    active_intents = []
    expired_count = 0
    
    for intent in intents:
        expire_at = intent.get('expire_at')
        
        if expire_at:
            try:
                # Поддержка разных форматов даты
                if isinstance(expire_at, str):
                    # ISO format: 2026-01-01T00:00:00Z
                    if 'T' in expire_at:
                        expire_date = datetime.fromisoformat(expire_at.replace('Z', '+00:00'))
                    else:
                        # Simple date: 2026-01-01
                        expire_date = datetime.strptime(expire_at, '%Y-%m-%d')
                    
                    if expire_date < datetime.now():
                        expired_count += 1
                        continue
                elif isinstance(expire_at, (int, float)):
                    # Unix timestamp
                    expire_date = datetime.fromtimestamp(expire_at)
                    if expire_date < datetime.now():
                        expired_count += 1
                        continue
            except (ValueError, TypeError) as e:
                # Если не можем распарсить дату, считаем интент активным
                pass
        
        active_intents.append(intent)
    
    return active_intents, expired_count

def get_version_statistics(intents: List[Dict[str, Any]]) -> Dict[str, int]:
    """
    Получает статистику по версиям интентов
    
    Args:
        intents: Список интентов
    
    Returns:
        Dict с полями: with_version, with_expire, active, expired
    """
    stats = {
        'with_version': 0,
        'with_expire': 0,
        'active': 0,
        'expired': 0
    }
    
    for intent in intents:
        # Подсчёт интентов с версией
        if 'version' in intent:
            stats['with_version'] += 1
        
        # Подсчёт интентов с expire_at
        if 'expire_at' in intent:
            stats['with_expire'] += 1
            
            # Проверяем истёк ли
            try:
                expire_at = intent['expire_at']
                is_expired = False
                
                if isinstance(expire_at, str):
                    if 'T' in expire_at:
                        expire_date = datetime.fromisoformat(expire_at.replace('Z', '+00:00'))
                    else:
                        expire_date = datetime.strptime(expire_at, '%Y-%m-%d')
                    is_expired = expire_date < datetime.now()
                elif isinstance(expire_at, (int, float)):
                    expire_date = datetime.fromtimestamp(expire_at)
                    is_expired = expire_date < datetime.now()
                
                if is_expired:
                    stats['expired'] += 1
                else:
                    stats['active'] += 1
            except (ValueError, TypeError):
                # Если не можем распарсить, считаем активным
                stats['active'] += 1
        else:
            # Без expire_at считаем активным
            stats['active'] += 1
    
    return stats
