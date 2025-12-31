#!/usr/bin/env python3
"""
Quick API compatibility test
Verifies that all generated schemas can be loaded by the FastAPI backend
"""

import json
from pathlib import Path
import sys

def test_api_compatibility():
    """Test that all schemas are compatible with API structure"""
    
    schemas_dir = Path(__file__).parent.parent / "data" / "schemas"
    
    print("\n" + "="*70)
    print("API COMPATIBILITY TEST")
    print("="*70)
    
    schema_files = list(schemas_dir.glob("*.json"))
    print(f"\nFound {len(schema_files)} schemas\n")
    
    all_ok = True
    stats = {
        'total_schemas': len(schema_files),
        'total_fields': 0,
        'total_size': 0,
        'min_fields': float('inf'),
        'max_fields': 0,
    }
    
    for schema_file in sorted(schema_files):
        try:
            with open(schema_file, 'r', encoding='utf-8') as f:
                schema = json.load(f)
            
            # Verify structure
            required = ['template_key', 'sheet_name', 'fields']
            for req in required:
                if req not in schema:
                    print(f"❌ {schema_file.name}: Missing {req}")
                    all_ok = False
                    continue
            
            field_count = len(schema['fields'])
            file_size = schema_file.stat().st_size
            
            stats['total_fields'] += field_count
            stats['total_size'] += file_size
            stats['min_fields'] = min(stats['min_fields'], field_count)
            stats['max_fields'] = max(stats['max_fields'], field_count)
            
            print(f"✅ {schema['template_key']:<30} | Fields: {field_count:>3} | Size: {file_size:>6} bytes")
            
        except Exception as e:
            print(f"❌ {schema_file.name}: {e}")
            all_ok = False
    
    print("\n" + "-"*70)
    print("STATISTICS")
    print("-"*70)
    print(f"Total schemas:    {stats['total_schemas']}")
    print(f"Total fields:     {stats['total_fields']:,}")
    print(f"Min fields:       {stats['min_fields']}")
    print(f"Max fields:       {stats['max_fields']}")
    print(f"Avg fields:       {stats['total_fields'] // stats['total_schemas']}")
    print(f"Total size:       {stats['total_size']:,} bytes ({stats['total_size']/1024:.1f} KB)")
    
    print("\n" + "="*70)
    if all_ok:
        print("✅ ALL SCHEMAS ARE API-COMPATIBLE")
        print("="*70 + "\n")
        return True
    else:
        print("❌ SOME SCHEMAS HAVE ISSUES")
        print("="*70 + "\n")
        return False

if __name__ == "__main__":
    success = test_api_compatibility()
    sys.exit(0 if success else 1)
