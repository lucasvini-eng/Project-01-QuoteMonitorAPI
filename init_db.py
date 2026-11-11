"""
Script para inicializar o banco de dados SQLite e importar as cotações da planilha.
Execute: python init_db.py
"""
import sys
from database import init_db, sync_sheets_to_sqlite, count_quotes, get_latest_quotes

def main():
    print("Iniciando banco de dados SQLite...")
    init_db()
    print("Sincronizando cotações da planilha do Google Sheets...")
    result = sync_sheets_to_sqlite()
    print(f"Status: {result.get('status')}")
    print(f"Fonte dos dados: {result.get('source')}")
    print(f"Registros processados: {result.get('processed_records')}")
    if result.get("note"):
        print(f"Nota/Aviso: {result.get('note')}")
    
    total = count_quotes()
    print(f"\nTotal de registros armazenados no SQLite: {total}")
    
    print("\nÚltimas cotações por moeda:")
    for q in get_latest_quotes():
        print(f" - {q['currency']}: R$ {q['quote_value']} ({q['percent_change']:+.2f}%) em {q['datetime']}")

if __name__ == "__main__":
    main()

