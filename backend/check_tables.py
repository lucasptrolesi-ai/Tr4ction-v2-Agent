import sqlite3

conn = sqlite3.connect('data/tr4ction.db')
cursor = conn.cursor()
cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
tables = cursor.fetchall()

print("Tabelas no banco de dados:")
print("=" * 50)
for table in tables:
    print(f"  - {table[0]}")
    
    # Ver schema da tabela
    cursor.execute(f"PRAGMA table_info({table[0]})")
    columns = cursor.fetchall()
    if table[0] in ['template_definitions', 'fillable_fields']:
        print(f"\n    Colunas:")
        for col in columns:
            print(f"      {col[1]} ({col[2]})")
        print()

conn.close()
