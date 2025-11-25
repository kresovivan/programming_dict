# check_db.py
import sqlite3
import os


def check_database():
    db_path = 'dictionaries.db'

    if not os.path.exists(db_path):
        print(f"❌ Файл {db_path} не существует")
        return

    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # Проверим таблицы
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = cursor.fetchall()
        print("📊 Таблицы в базе:")
        for table in tables:
            print(f"  - {table[0]}")

        # Проверим структуру таблицы words
        if 'words' in [table[0] for table in tables]:
            print("\n📊 Структура таблицы 'words':")
            cursor.execute("PRAGMA table_info(words)")
            columns = cursor.fetchall()
            for col in columns:
                print(f"  - {col[1]} ({col[2]})")

            # Проверим данные
            print("\n📊 Пример данных в 'words':")
            cursor.execute("SELECT * FROM words LIMIT 3")
            rows = cursor.fetchall()
            for row in rows:
                print(f"  - {row}")

        conn.close()

    except Exception as e:
        print(f"❌ Ошибка: {e}")


if __name__ == '__main__':
    check_database()