# Импорт необходимых модулей
from flask import Flask, render_template, request, jsonify  # Flask и его компоненты
import sqlite3  # Для работы с SQLite базой данных
import os  # Для работы с файловой системой
from typing import List, Dict  # Для аннотации типов

# Создание экземпляра Flask приложения
app = Flask(__name__)


class DictionaryManager:
    """
    Класс для управления словарем терминов из базы данных SQLite.
    Реализует паттерн Single Responsibility Principle (SRP).
    """

    def __init__(self):
        """Инициализация менеджера словаря."""
        self.db_path = r'C:\sqllite\dictionaries.db'  # Путь к базе данных
        self.learned_terms = set()  # Множество для хранения изученных терминов
        # Загрузка терминов происходит только при первом обращении через свойство

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
            conn = sqlite3.connect(self.db_path)  # Установка соединения
            conn.row_factory = sqlite3.Row  # Настройка для доступа к колонкам по имени
            return conn
        except sqlite3.Error as e:
            print(f"Ошибка подключения к базе данных: {e}")
            return None

    def _validate_database(self) -> bool:
        """
        Проверка существования базы данных и таблицы words.

        Returns:
            bool: True если база данных и таблица существуют, иначе False
        """
        # Проверка существования файла базы данных
        if not os.path.exists(self.db_path):
            print(f"Файл базы данных {self.db_path} не найден.")
            return False

        conn = self._get_db_connection()
        if conn is None:
            return False

        try:
            cursor = conn.cursor()
            # Проверка существования таблицы words
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='words'")
            table_exists = cursor.fetchone() is not None
            conn.close()
            return table_exists
        except sqlite3.Error as e:
            print(f"Ошибка при проверке таблицы: {e}")
            conn.close()
            return False

    def _load_terms_from_db(self) -> List[Dict]:
        """
        Приватный метод загрузки терминов из базы данных.

        Returns:
            List[Dict]: Список словарей с терминами
        """
        # Валидация базы данных перед загрузкой
        if not self._validate_database():
            return []

        conn = self._get_db_connection()
        if conn is None:
            return []

        try:
            cursor = conn.cursor()
            # SQL запрос для получения всех терминов
            cursor.execute("SELECT term, definition, translation, category, level FROM words")
            rows = cursor.fetchall()

            terms = []
            for row in rows:
                # Обработка каждой строки результата
                term_dict = self._process_term_row(row)
                if term_dict:  # Добавляем только валидные термины
                    terms.append(term_dict)

            print(f"Успешно загружено {len(terms)} терминов из базы данных")
            return terms

        except sqlite3.Error as e:
            print(f"Ошибка при загрузке терминов: {e}")
            return []
        finally:
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
            print(f"Ошибка обработки строки термина: {e}")
            return None

    def get_categories(self) -> List[str]:
        """
        Получение уникального списка категорий из базы данных.

        Returns:
            List[str]: Список категорий в алфавитном порядке
        """
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
            return categories
        except sqlite3.Error as e:
            print(f"Ошибка при получении категорий: {e}")
            return []
        finally:
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
            print(f"Ошибка при фильтрации терминов: {e}")
            return []
        finally:
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
            print(f"Ошибка при получении количества терминов: {e}")
            return 0
        finally:
            conn.close()


# Инициализация единственного экземпляра менеджера словаря
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


# Точка входа при запуске скрипта напрямую
if __name__ == '__main__':
    # Запуск Flask приложения
    app.run(host='0.0.0.0', port=5000, debug=True)