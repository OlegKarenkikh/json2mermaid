# utils/loaders.py v5.1 ROBUST PARSING
import json
import os
from typing import List, Dict, Any, Optional, Tuple

def load_intents(filepath: str, max_lines: Optional[int] = None) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
    """Загружает интенты из JSONL или JSON с ROBUST парсингом"""
    from .config import MAX_LINES, FILTER_EXPIRED
    from .version_manager import filter_expired_intents, get_version_statistics
    
    if max_lines is None:
        max_lines = MAX_LINES if MAX_LINES > 0 else 1000000
    
    if not os.path.exists(filepath):
        print(f"❌ Файл не найден: {filepath}")
        return [], {}
    
    file_size = os.path.getsize(filepath)
    print(f"📂 Loading data from: {filepath}")
    print(f"   Size: {file_size:,} bytes ({file_size/1024/1024:.2f} MB)")
    
    intents = []
    total_lines = 0
    errors = {
        'empty': 0,
        'fixed': 0,
        'skipped': 0,
        'success': 0
    }
    
    # ========================================================================
    # ПОПЫТКА 1: JSON массив (весь файл целиком)
    # ========================================================================
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
            
        if isinstance(data, list):
            print(f"✅ Loaded as JSON array: {len(data)} records")
            intents = data[:max_lines]
            errors['success'] = len(intents)
        elif isinstance(data, dict):
            if 'intents' in data:
                print(f"✅ Loaded from 'intents' key: {len(data['intents'])} records")
                intents = data['intents'][:max_lines]
                errors['success'] = len(intents)
            else:
                print(f"✅ Loaded single dict as 1 record")
                intents = [data]
                errors['success'] = 1
                
        # Если успешно загрузили, возвращаем
        if intents:
            metadata = _build_metadata(filepath, intents, errors, total_lines)
            return _apply_filters(intents, metadata)
            
    except json.JSONDecodeError:
        pass  # Пробуем следующий метод
    except Exception as e:
        print(f"⚠️  Attempt 1 (JSON array) failed: {e}")
    
    # ========================================================================
    # ПОПЫТКА 2: JSONL построчно с ROBUST парсингом
    # ========================================================================
    try:
        print("📖 Trying JSONL line-by-line with robust parsing...")
        intents = []
        
        with open(filepath, 'r', encoding='utf-8') as f:
            for line_num, line in enumerate(f, 1):
                total_lines += 1
                line = line.strip()
                
                # Пропускаем пустые и комментарии
                if not line or line.startswith('#') or line.startswith('//'):
                    errors['empty'] += 1
                    continue
                
                # Стандартный парсинг
                try:
                    obj = json.loads(line)
                    if isinstance(obj, dict):
                        intents.append(obj)
                        errors['success'] += 1
                    continue
                    
                except json.JSONDecodeError as e:
                    # ROBUST: Пытаемся извлечь через raw_decode (Extra data)
                    try:
                        decoder = json.JSONDecoder()
                        remaining = line
                        extracted = False
                        
                        while remaining:
                            remaining = remaining.strip()
                            if not remaining:
                                break
                            
                            try:
                                obj, idx = decoder.raw_decode(remaining)
                                if isinstance(obj, dict):
                                    intents.append(obj)
                                    errors['fixed'] += 1
                                    extracted = True
                                remaining = remaining[idx:]
                            except Exception:
                                break
                        
                        if not extracted:
                            # Выводим первые 10 ошибок для отладки
                            if errors['skipped'] < 10:
                                print(f"⚠️  Line {line_num}: JSON decode error - {str(e)}")
                            errors['skipped'] += 1
                            
                    except Exception:
                        if errors['skipped'] < 10:
                            print(f"⚠️  Line {line_num}: JSON decode error - {str(e)}")
                        errors['skipped'] += 1
                
                # Защита от огромных файлов
                if len(intents) >= max_lines:
                    print(f"⚠️  Reached max_lines limit: {max_lines}")
                    break
        
        # Статистика
        if intents:
            print(f"✅ Successfully loaded: {errors['success']} records")
            if errors['fixed'] > 0:
                print(f"🔧 Fixed (Extra data): {errors['fixed']} records")
            if errors['empty'] > 0:
                print(f"⚪ Skipped (empty/comments): {errors['empty']} lines")
            if errors['skipped'] > 0:
                print(f"⚠️  Skipped (invalid JSON): {errors['skipped']} lines")
            if errors['skipped'] > 10:
                print(f"   (showing first 10 errors only)")
            print(f"📝 Total lines processed: {total_lines}")
            
            metadata = _build_metadata(filepath, intents, errors, total_lines)
            return _apply_filters(intents, metadata)
        else:
            print(f"❌ Could not load any valid JSON objects")
            print(f"📝 Lines processed: {total_lines}")
            print(f"⚠️  Skipped: {errors['skipped']}")
            return [], {}
            
    except Exception as e:
        print(f"❌ Error loading file: {e}")
        return [], {}

def _build_metadata(filepath: str, intents: List[Dict], errors: Dict, total_lines: int) -> Dict:
    """Построение метаданных загрузки"""
    return {
        'source_file': filepath,
        'total_loaded': len(intents),
        'total_lines_processed': total_lines,
        'parsing_stats': {
            'success': errors['success'],
            'fixed_extra_data': errors['fixed'],
            'skipped_empty': errors['empty'],
            'skipped_invalid': errors['skipped']
        }
    }

def _apply_filters(intents: List[Dict], metadata: Dict) -> Tuple[List[Dict], Dict]:
    """Применение фильтров (expired и т.д.)"""
    from .config import FILTER_EXPIRED
    from .version_manager import filter_expired_intents, get_version_statistics
    
    if FILTER_EXPIRED:
        active_intents, expired_count = filter_expired_intents(intents)
        if expired_count > 0:
            print(f"⚠️  Filtered expired: {expired_count} records")
            metadata['filtered_expired'] = expired_count
        intents = active_intents
    
    metadata['final_count'] = len(intents)
    metadata['version_statistics'] = get_version_statistics(intents)
    
    return intents, metadata
