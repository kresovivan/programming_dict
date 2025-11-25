import sqlite3
import csv
import os
from pathlib import Path


def create_database():
    """Создает базу данных и таблицу words"""
    db_path = Path("C:/sqllite/dictionaries.db")

    # Создаем папку если не существует
    db_path.parent.mkdir(parents=True, exist_ok=True)

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Создаем таблицу words
    cursor.execute('''
                   CREATE TABLE IF NOT EXISTS words
                   (
                       id
                       INTEGER
                       PRIMARY
                       KEY
                       AUTOINCREMENT,
                       term
                       TEXT
                       NOT
                       NULL,
                       definition
                       TEXT
                       NOT
                       NULL,
                       translation
                       TEXT
                       NOT
                       NULL,
                       category
                       TEXT,
                       level
                       TEXT,
                       created_at
                       TIMESTAMP
                       DEFAULT
                       CURRENT_TIMESTAMP
                   )
                   ''')

    # Создаем индекс для быстрого поиска
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_term ON words(term)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_category ON words(category)')

    conn.commit()
    return conn


def load_words_from_csv(csv_file_path):
    """Загружает слова из CSV файла"""
    words_data = []

    try:
        with open(csv_file_path, 'r', encoding='utf-8') as csv_file:
            csv_reader = csv.DictReader(csv_file)

            for row in csv_reader:
                # Обрабатываем каждую строку CSV
                word = {
                    'term': row.get('term', '').strip(),
                    'definition': row.get('definition', '').strip(),
                    'translation': row.get('translation', '').strip(),
                    'category': row.get('category', '').strip(),
                    'level': row.get('level', '').strip()
                }
                words_data.append(word)

        print(f"✅ Успешно загружено {len(words_data)} слов из файла {csv_file_path}")
        return words_data

    except FileNotFoundError:
        print(f"❌ Файл {csv_file_path} не найден")
        return []
    except Exception as e:
        print(f"❌ Ошибка при чтении CSV файла: {e}")
        return []


def insert_words(conn, words_data):
    """Вставляет слова в базу данных"""
    cursor = conn.cursor()

    # SQL запрос для вставки
    insert_query = '''
                   INSERT INTO words (term, definition, translation, category, level)
                   VALUES (?, ?, ?, ?, ?) \
                   '''

    try:
        # Вставляем все слова
        cursor.executemany(insert_query, [
            (word['term'], word['definition'], word['translation'], word['category'], word['level'])
            for word in words_data
        ])

        conn.commit()
        print(f"✅ Успешно добавлено {cursor.rowcount} слов в базу данных")
        return True

    except sqlite3.Error as e:
        print(f"❌ Ошибка при вставке данных: {e}")
        conn.rollback()
        return False


def count_words(conn):
    """Подсчитывает количество слов в базе"""
    cursor = conn.cursor()
    cursor.execute('SELECT COUNT(*) FROM words')
    count = cursor.fetchone()[0]
    return count


def show_categories(conn):
    """Показывает категории и количество слов в каждой"""
    cursor = conn.cursor()
    cursor.execute('''
                   SELECT category, COUNT(*) as count
                   FROM words
                   GROUP BY category
                   ORDER BY count DESC
                   ''')

    print("\n📊 Статистика по категориям:")
    for category, count in cursor.fetchall():
        print(f"  {category}: {count} слов")


def show_sample_data(conn, limit=5):
    """Показывает пример данных из базы"""
    cursor = conn.cursor()
    cursor.execute('SELECT term, translation, category, level FROM words LIMIT ?', (limit,))

    print(f"\n📝 Пример данных (первые {limit} записей):")
    for term, translation, category, level in cursor.fetchall():
        print(f"  {term} -> {translation} | {category} | {level}")


def main():
    """Основная функция"""
    print("🚀 Начинаем загрузку слов в базу данных...")

    # Путь к CSV файлу с данными
    csv_file_path = "words_data.csv"  # Вы можете изменить путь к файлу

    # Проверяем существование CSV файла
    if not os.path.exists(csv_file_path):
        print(f"❌ CSV файл {csv_file_path} не найден!")
        print("Создайте файл words_data.csv со следующими колонками:")
        print("term,definition,translation,category,level")
        return

    # Загружаем слова из CSV файла
    words_data = load_words_from_csv(csv_file_path)

    if not words_data:
        print("❌ Не удалось загрузить данные из CSV файла")
        return

    try:
        # Создаем базу данных и таблицу
        conn = create_database()
        print("✅ База данных и таблица созданы/проверены")

        # Вставляем слова
        if insert_words(conn, words_data):
            # Показываем статистику
            total_words = count_words(conn)
            print(f"📈 Всего слов в базе: {total_words}")

            show_categories(conn)
            show_sample_data(conn)

            print(f"\n🎉 База данных успешно создана по пути: C:/sqllite/dictionaries.db")

    except Exception as e:
        print(f"❌ Критическая ошибка: {e}")

    finally:
        # Закрываем соединение
        if 'conn' in locals():
            conn.close()
            print("🔒 Соединение с базой данных закрыто")


def test_connection():
    """Тестирует соединение с базой данных"""
    try:
        conn = sqlite3.connect("C:/sqllite/dictionaries.db")
        cursor = conn.cursor()

        # Проверяем существование таблицы
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='words'")
        table_exists = cursor.fetchone()

        if table_exists:
            print("✅ Таблица 'words' существует")
            count = count_words(conn)
            print(f"✅ Количество записей в таблице: {count}")
        else:
            print("❌ Таблица 'words' не найдена")

        conn.close()

    except Exception as e:
        print(f"❌ Ошибка при тестировании: {e}")


if __name__ == "__main__":
    main()

    # Опционально: тестирование после выполнения
    print("\n" + "=" * 50)
    print("🧪 Тестирование базы данных...")
    test_connection()