# Импорт необходимых модулей
from flask import Flask, render_template, request, jsonify  # Flask и его компоненты
import sqlite3  # Для работы с SQLite базой данных
import os  # Для работы с файловой системой
from typing import List, Dict  # Для аннотации типов

# Создание экземпляра Flask приложения
app = Flask(__name__)


class DictionaryManager:
    def __init__(self):
        """Инициализация менеджера словаря."""
        # Создаем папку 'data' рядом со скриптом и помещаем туда БД
        base_dir = os.path.dirname(os.path.abspath(__file__))
        db_dir = os.path.join(base_dir, 'data')

        # Создаем папку, если её нет
        os.makedirs(db_dir, exist_ok=True)

        self.db_path = os.path.join(db_dir, 'dictionaries.db')
        self.learned_terms = set()

        print(f"🔍 ДИАГНОСТИКА БАЗЫ ДАННЫХ")
        print(f"📁 Путь к БД: {self.db_path}")
        print(f"📁 Файл БД существует: {os.path.exists(self.db_path)}")

        # Запускаем полную диагностику и инициализацию
        self._initialize_database()

    def _initialize_database(self):
        """Инициализирует базу данных: создает таблицу если её нет."""
        print(f"\n🔍 ИНИЦИАЛИЗАЦИЯ БАЗЫ ДАННЫХ...")

        # Проверка существования файла
        if not os.path.exists(self.db_path):
            print(f"📝 Файл базы данных не существует. Создаем новый...")
            self._create_database()
            return

        # Проверка размера файла
        file_size = os.path.getsize(self.db_path)
        print(f"📊 Размер файла БД: {file_size} байт")

        if file_size == 0:
            print(f"📝 Файл базы данных пустой. Создаем структуру...")
            self._create_database()
            return

        # Проверяем существование таблицы words
        conn = self._get_db_connection()
        if conn is None:
            print(f"❌ Не удалось подключиться к базе данных")
            return

        try:
            cursor = conn.cursor()

            # Проверяем все таблицы в базе
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = cursor.fetchall()
            table_names = [table['name'] for table in tables]
            print(f"📋 Все таблицы в базе: {table_names}")

            # Если таблица words не существует, создаем её
            if 'words' not in table_names:
                print(f"📝 Таблица 'words' не найдена. Создаем...")
                self._create_words_table(conn)
            else:
                print(f"✅ Таблица 'words' найдена!")

                # Проверяем структуру таблицы
                cursor.execute("PRAGMA table_info(words)")
                columns = cursor.fetchall()
                print(f"📊 Структура таблицы 'words':")
                for col in columns:
                    print(f"   - {col['name']} ({col['type']})")

        except sqlite3.Error as e:
            print(f"❌ Ошибка при инициализации БД: {e}")
        finally:
            if conn:
                conn.close()


    def _run_detailed_diagnostics(self):
        """Запускает детальную диагностику базы данных."""
        print(f"\n🔍 ЗАПУСК ДЕТАЛЬНОЙ ДИАГНОСТИКИ...")

        # Проверка существования файла
        if not os.path.exists(self.db_path):
            print(f"❌ Файл базы данных не существует!")
            print(f"💡 Решение: Создайте базу данных или проверьте путь")
            return

        # Проверка размера файла
        file_size = os.path.getsize(self.db_path)
        print(f"📊 Размер файла БД: {file_size} байт")

        if file_size == 0:
            print(f"❌ Файл базы данных пустой!")
            print(f"💡 Решение: База данных не инициализирована")
            return

        # ПРОВЕРКА ПРАВ ДОСТУПА К ФАЙЛУ
        print(f"\n🔐 ПРОВЕРКА ПРАВ ДОСТУПА К ФАЙЛУ:")
        try:
            # Проверяем права на чтение
            can_read = os.access(self.db_path, os.R_OK)
            print(f"📖 Право на чтение: {'✅ ЕСТЬ' if can_read else '❌ НЕТ'}")

            # Проверяем права на запись
            can_write = os.access(self.db_path, os.W_OK)
            print(f"📝 Право на запись: {'✅ ЕСТЬ' if can_write else '❌ НЕТ'}")

            # Проверяем права на выполнение (для директории)
            can_execute = os.access(os.path.dirname(self.db_path), os.X_OK)
            print(f"📁 Право на доступ к папке: {'✅ ЕСТЬ' if can_execute else '❌ НЕТ'}")

            if not can_read:
                print(f"🚨 КРИТИЧЕСКАЯ ОШИБКА: Нет прав на чтение файла БД!")
                return

        except Exception as e:
            print(f"❌ Ошибка при проверке прав доступа: {e}")

        # Проверка подключения и структуры БД
        conn = self._get_db_connection()
        if conn is None:
            print(f"❌ Не удалось подключиться к базе данных")
            return

        try:
            cursor = conn.cursor()

            # 1. Проверяем все таблицы в базе
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = cursor.fetchall()
            table_names = [table['name'] for table in tables]
            print(f"📋 Все таблицы в базе: {table_names}")

            # 2. Если таблица words существует, проверяем её структуру
            if 'words' in table_names:
                print(f"✅ Таблица 'words' найдена!")

                # Проверяем структуру таблицы words
                cursor.execute("PRAGMA table_info(words)")
                columns = cursor.fetchall()
                print(f"📊 Структура таблицы 'words':")
                for col in columns:
                    print(f"   - {col['name']} ({col['type']})")

                # Проверяем количество записей
                cursor.execute("SELECT COUNT(*) as count FROM words")
                count_result = cursor.fetchone()
                record_count = count_result['count']
                print(f"📊 Количество записей в таблице 'words': {record_count}")

                # ДЕТАЛЬНАЯ ПРОВЕРКА ПРАВ ДОСТУПА К ТАБЛИЦЕ
                print(f"\n🔐 ДЕТАЛЬНАЯ ПРОВЕРКА ДОСТУПА К ТАБЛИЦЕ:")

                # Проверяем SELECT доступ
                try:
                    cursor.execute("SELECT 1 FROM words LIMIT 1")
                    test_result = cursor.fetchone()
                    print(f"✅ SELECT доступ: ЕСТЬ (может читать данные)")
                except sqlite3.Error as e:
                    print(f"❌ SELECT доступ: ОШИБКА - {e}")

                # Проверяем доступ к конкретным колонкам
                try:
                    cursor.execute("SELECT term, definition FROM words LIMIT 1")
                    test_result = cursor.fetchone()
                    print(f"✅ Доступ к колонкам term,definition: ЕСТЬ")
                except sqlite3.Error as e:
                    print(f"❌ Доступ к колонкам term,definition: ОШИБКА - {e}")

                # Проверяем доступ ко всем колонкам которые используем
                try:
                    cursor.execute("SELECT term, definition, translation, category, level FROM words LIMIT 1")
                    test_result = cursor.fetchone()
                    print(f"✅ Доступ ко всем нужным колонкам: ЕСТЬ")
                except sqlite3.Error as e:
                    print(f"❌ Доступ ко всем нужным колонкам: ОШИБКА - {e}")

                # Если есть записи, показываем пример данных
                if record_count > 0:
                    try:
                        cursor.execute("SELECT * FROM words LIMIT 3")
                        sample_records = cursor.fetchall()
                        print(f"\n📝 ПЕРВЫЕ 3 ЗАПИСИ В ТАБЛИЦЕ:")
                        for i, record in enumerate(sample_records):
                            print(f"   Запись {i + 1}: {dict(record)}")
                    except sqlite3.Error as e:
                        print(f"❌ Не удалось прочитать примеры данных: {e}")
                else:
                    print(f"ℹ️ Таблица существует, но пустая")

            else:
                print(f"❌ Таблица 'words' не найдена!")
                print(f"💡 Решение: Создайте таблицу words с нужной структурой")

            # 3. Проверяем другие системные таблицы
            print(f"\n🔍 Дополнительная информация:")
            cursor.execute("SELECT sqlite_version()")
            version = cursor.fetchone()
            print(f"📊 Версия SQLite: {version[0]}")

        except sqlite3.Error as e:
            print(f"❌ Ошибка при диагностике БД: {e}")
            import traceback
            traceback.print_exc()
        finally:
            if conn:
                conn.close()

    @property
    def terms(self) -> List[Dict]:
        """
        Свойство для ленивой загрузки терминов.
        Загружает термины только при первом обращении.
        """
        if not hasattr(self, '_terms'):
            self._terms = self._load_terms_from_db()
        return self._terms

    def _get_db_connection(self) -> sqlite3.Connection:
        """
        Приватный метод для установления соединения с базой данных.

        Returns:
            sqlite3.Connection: Объект соединения с базой данных или None при ошибке
        """
        try:
            # Дополнительная проверка перед подключением
            if not os.path.exists(self.db_path):
                print(f"❌ Файл БД не существует: {self.db_path}")
                return None

            if not os.access(self.db_path, os.R_OK):
                print(f"❌ Нет прав на чтение файла БД: {self.db_path}")
                return None

            conn = sqlite3.connect(self.db_path)  # Установка соединения
            conn.row_factory = sqlite3.Row  # Настройка для доступа к колонкам по имени
            return conn
        except sqlite3.Error as e:
            print(f"❌ Ошибка подключения к базе данных: {e}")
            import traceback
            traceback.print_exc()
            return None

    def _validate_database(self) -> bool:
        """
        Проверка существования базы данных и таблицы words.

        Returns:
            bool: True если база данных и таблица существуют, иначе False
        """
        # Проверка существования файла базы данных
        if not os.path.exists(self.db_path):
            print(f"❌ Файл базы данных {self.db_path} не найден.")
            return False

        conn = self._get_db_connection()
        if conn is None:
            return False

        try:
            cursor = conn.cursor()
            # Проверка существования таблицы words
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='words'")
            table_exists = cursor.fetchone() is not None

            if not table_exists:
                print(f"❌ Таблица 'words' не существует в базе данных")
            else:
                print(f"✅ Таблица 'words' существует")

            conn.close()
            return table_exists
        except sqlite3.Error as e:
            print(f"❌ Ошибка при проверке таблицы: {e}")
            conn.close()
            return False

    def _load_terms_from_db(self) -> List[Dict]:
        """
        Приватный метод загрузки терминов из базы данных.

        Returns:
            List[Dict]: Список словарей с терминами
        """
        print(f"\n🔍 ЗАГРУЗКА ТЕРМИНОВ ИЗ БАЗЫ ДАННЫХ...")

        # Дополнительная проверка прав доступа
        if not os.access(self.db_path, os.R_OK):
            print(f"🚨 КРИТИЧЕСКАЯ ОШИБКА: Нет прав на чтение файла БД!")
            return []

        # Валидация базы данных перед загрузкой
        if not self._validate_database():
            print(f"❌ Валидация базы данных не пройдена")
            return []

        conn = self._get_db_connection()
        if conn is None:
            print(f"❌ Не удалось подключиться к базе данных")
            return []

        try:
            cursor = conn.cursor()
            # SQL запрос для получения всех терминов
            print(f"🔍 Выполнение запроса к таблице words...")
            cursor.execute("SELECT term, definition, translation, category, level FROM words")
            rows = cursor.fetchall()
            print(f"🔍 Получено строк: {len(rows)}")

            terms = []
            for row in rows:
                # Обработка каждой строки результата
                term_dict = self._process_term_row(row)
                if term_dict:  # Добавляем только валидные термины
                    terms.append(term_dict)

            print(f"✅ Успешно загружено {len(terms)} терминов из базы данных")
            return terms

        except sqlite3.Error as e:
            print(f"❌ Ошибка при загрузке терминов: {e}")
            import traceback
            traceback.print_exc()
            return []
        finally:
            if conn:
                conn.close()  # Гарантированное закрытие соединения

    def _process_term_row(self, row: sqlite3.Row) -> Dict:
        """
        Обработка строки результата запроса к базе данных.

        Args:
            row: Строка результата SQL запроса

        Returns:
            Dict: Словарь с данными термина или None для невалидных строк
        """
        try:
            # Создание словаря с обработкой None значений
            term_dict = {
                "term": row['term'] or "",  # Использование or для обработки None
                "definition": row['definition'] or "",
                "translation": row['translation'] or "",
                "category": row['category'] or "Другое",
                "level": row['level'] or "Medium"
            }

            # Пропуск терминов без названия или определения
            if not term_dict["term"] or not term_dict["definition"]:
                return None

            return term_dict

        except Exception as e:
            print(f"❌ Ошибка обработки строки термина: {e}")
            return None

    def get_categories(self) -> List[str]:
        """
        Получение уникального списка категорий из базы данных.

        Returns:
            List[str]: Список категорий в алфавитном порядке
        """
        print(f"🔍 Получение списка категорий...")
        conn = self._get_db_connection()
        if conn is None:
            return []

        try:
            cursor = conn.cursor()
            # SQL запрос для получения уникальных категорий
            cursor.execute("SELECT DISTINCT category FROM words WHERE category IS NOT NULL ORDER BY category")
            rows = cursor.fetchall()
            # Преобразование результатов в список строк
            categories = [row['category'] for row in rows]
            print(f"✅ Получено категорий: {len(categories)}")
            return categories
        except sqlite3.Error as e:
            print(f"❌ Ошибка при получении категорий: {e}")
            return []
        finally:
            if conn:
                conn.close()

    def filter_terms(self, category: str = "Все", search_query: str = "") -> List[Dict]:
        """
        Фильтрация терминов по категории и поисковому запросу.

        Args:
            category: Категория для фильтрации ("Все" для всех категорий)
            search_query: Строка для поиска по терминам, переводу и определению

        Returns:
            List[Dict]: Отфильтрованный список терминов
        """
        conn = self._get_db_connection()
        if conn is None:
            return []

        try:
            cursor = conn.cursor()

            # Базовый SQL запрос с условием 1=1 для удобства добавления фильтров
            query = "SELECT term, definition, translation, category, level FROM words WHERE 1=1"
            params = []

            # Добавление фильтра по категории если указана
            if category != "Все":
                query += " AND category = ?"
                params.append(category)

            # Добавление поиска по всем текстовым полям если указан запрос
            if search_query.strip():
                search_pattern = f"%{search_query}%"
                query += " AND (term LIKE ? OR translation LIKE ? OR definition LIKE ?)"
                params.extend([search_pattern] * 3)  # Три одинаковых параметра для трех полей

            cursor.execute(query, params)
            rows = cursor.fetchall()

            # Преобразование результатов в список словарей
            filtered_terms = []
            for row in rows:
                term_dict = self._process_term_row(row)
                if term_dict:
                    filtered_terms.append(term_dict)

            return filtered_terms

        except sqlite3.Error as e:
            print(f"❌ Ошибка при фильтрации терминов: {e}")
            return []
        finally:
            if conn:
                conn.close()

    def get_total_terms_count(self) -> int:
        """
        Получение общего количества терминов в базе данных.

        Returns:
            int: Количество терминов
        """
        conn = self._get_db_connection()
        if conn is None:
            return 0

        try:
            cursor = conn.cursor()
            # SQL запрос для подсчета всех записей
            cursor.execute("SELECT COUNT(*) as count FROM words")
            result = cursor.fetchone()
            return result['count'] if result else 0
        except sqlite3.Error as e:
            print(f"❌ Ошибка при получении количества терминов: {e}")
            return 0
        finally:
            if conn:
                conn.close()


# Инициализация единственного экземпляра менеджера словаря
print("🚀 ИНИЦИАЛИЗАЦИЯ ПРИЛОЖЕНИЯ...")
dict_manager = DictionaryManager()


@app.route('/')
def index():
    """
    Обработчик главной страницы приложения.

    Returns:
        rendered_template: HTML страница с терминами и статистикой
    """
    # Получение данных для отображения
    categories = dict_manager.get_categories()
    terms = dict_manager.filter_terms()
    progress_total = dict_manager.get_total_terms_count()
    progress_learned = len(dict_manager.learned_terms)

    # Расчет процента изучения с защитой от деления на ноль
    progress_percentage = (progress_learned / progress_total * 100) if progress_total > 0 else 0

    # Рендеринг шаблона с передачей данных
    return render_template(
        'index.html',
        terms=terms,
        categories=categories,
        progress_total=progress_total,
        progress_learned=progress_learned,
        progress_percentage=progress_percentage
    )


@app.route('/filter')
def filter_terms():
    """
    API endpoint для AJAX фильтрации терминов.

    Returns:
        JSON: Отфильтрованный список терминов
    """
    # Получение параметров фильтрации из запроса
    category = request.args.get('category', 'Все')
    search_query = request.args.get('search', '')

    # Применение фильтров и возврат JSON ответа
    filtered_terms = dict_manager.filter_terms(category, search_query)
    return jsonify({'terms': filtered_terms})


@app.route('/learning')
def learning_mode():
    """
    Обработчик страницы режима обучения.

    Returns:
        rendered_template: HTML страница для обучения
    """
    # Получение параметров фильтрации
    category = request.args.get('category', 'Все')
    search_query = request.args.get('search', '')

    # Загрузка отфильтрованных терминов для обучения
    terms = dict_manager.filter_terms(category, search_query)
    return render_template('learning.html', terms=terms)


@app.route('/mark_learned', methods=['POST'])
def mark_learned():
    """
    API endpoint для отметки термина как изученного.

    Returns:
        JSON: Обновленная статистика прогресса
    """
    # Получение данных из JSON тела запроса
    data = request.get_json()
    term = data.get('term') if data else None

    # Добавление термина в множество изученных
    if term:
        dict_manager.learned_terms.add(term)

    # Расчет обновленной статистики
    progress_total = dict_manager.get_total_terms_count()
    progress_learned = len(dict_manager.learned_terms)
    progress_percentage = (progress_learned / progress_total * 100) if progress_total > 0 else 0

    # Возврат JSON с обновленной статистикой
    return jsonify({
        'progress_learned': progress_learned,
        'progress_total': progress_total,
        'progress_percentage': round(progress_percentage, 1)
    })


@app.route('/stats')
def get_stats():
    """
    API endpoint для получения статистики по категориям.

    Returns:
        JSON: Статистика изучения по категориям
    """
    categories = dict_manager.get_categories()
    stats = {}

    # Расчет статистики для каждой категории
    for category in categories:
        category_terms = dict_manager.filter_terms(category)
        # Подсчет изученных терминов в категории
        learned_count = len([term for term in category_terms if term["term"] in dict_manager.learned_terms])

        stats[category] = {
            'total': len(category_terms),
            'learned': learned_count,
            'percentage': (learned_count / len(category_terms) * 100) if len(category_terms) > 0 else 0
        }

    return jsonify(stats)



@app.route('/templates/index.html')
def templates_index():
    """Обработчик для страницы templates/index.html"""
    categories = dict_manager.get_categories()
    terms = dict_manager.filter_terms()
    progress_total = dict_manager.get_total_terms_count()
    progress_learned = len(dict_manager.learned_terms)
    progress_percentage = (progress_learned / progress_total * 100) if progress_total > 0 else 0

    return render_template(
        'index.html',
        terms=terms,
        categories=categories,
        progress_total=progress_total,
        progress_learned=progress_learned,
        progress_percentage=progress_percentage
    )

@app.route('/')
def main_index():
    """Основной обработчик для корневого URL"""
    categories = dict_manager.get_categories()
    terms = dict_manager.filter_terms()
    progress_total = dict_manager.get_total_terms_count()
    progress_learned = len(dict_manager.learned_terms)
    progress_percentage = (progress_learned / progress_total * 100) if progress_total > 0 else 0

    return render_template(
        'index.html',
        terms=terms,
        categories=categories,
        progress_total=progress_total,
        progress_learned=progress_learned,
        progress_percentage=progress_percentage
    )

# Точка входа при запуске скрипта напрямую
if __name__ == '__main__':
    # Запуск Flask приложения
    print("🚀 ЗАПУСК FLASK ПРИЛОЖЕНИЯ...")
    app.run(host='0.0.0.0', port=5000, debug=True)