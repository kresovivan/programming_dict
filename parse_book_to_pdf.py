#!/usr/bin/env python3
"""
Скрипт для извлечения технических терминов из PDF книг по программированию
Требуется: pip install pdfplumber nltk

Автоматически извлекает английские термины из PDF файлов и сохраняет:
1. Статистику с топ-100 слов и топ-50 терминов
2. Все термины для импорта в базу данных

Имя скрипта: pdf_term_extractor.py
"""

import pdfplumber
import re
import csv
import sys
import os
from pathlib import Path
from collections import Counter
import nltk
from nltk.corpus import stopwords

# ================================================
# НАСТРОЙКИ: Укажите путь к вашему PDF файлу здесь
# ================================================
# Укажите полный путь к PDF файлу для автоматической обработки
# Пример: PDF_FILE_PATH = r"C:\путь\к\вашему\файлу.pdf"
PDF_FILE_PATH = r"C:\Users\Kresov Ivan\PycharmProjects\programming_dict\t-building-etl-pipelines-with-python.pdf"
# ================================================

# Скачиваем стоп-слова для фильтрации (один раз)
try:
    nltk.data.find('corpora/stopwords')
except LookupError:
    print("Скачиваем стоп-слова NLTK...")
    nltk.download('stopwords')


def extract_technical_terms(pdf_path,
                            min_word_length=4,
                            min_frequency=2,
                            extract_camel_case=True):
    """
    Извлекает технические термины из PDF книги по программированию
    Возвращает словарь с результатами
    """
    all_words = []
    all_terms = []  # Для многословных терминов
    english_stopwords = set(stopwords.words('english'))

    pdf_path = Path(pdf_path)

    if not pdf_path.exists():
        print(f"❌ Ошибка: файл {pdf_path} не найден")
        print(f"   Проверьте путь: {pdf_path.absolute()}")
        return None

    print(f"📖 Обработка файла: {pdf_path.name}")
    print(f"📏 Минимальная длина слова: {min_word_length}")
    print(f"📊 Минимальная частота: {min_frequency}")

    try:
        with pdfplumber.open(pdf_path) as pdf:
            total_pages = len(pdf.pages)
            print(f"📄 Количество страниц: {total_pages}")

            for page_num, page in enumerate(pdf.pages):
                text = page.extract_text()

                if text:
                    # 1. Извлекаем отдельные слова
                    words = re.findall(r'\b[a-zA-Z]{' + str(min_word_length) + r',}\b', text.lower())
                    words = [word for word in words if word not in english_stopwords]
                    all_words.extend(words)

                    # 2. Извлекаем CamelCase термины (например, DataPipeline, ETLProcess)
                    if extract_camel_case:
                        camel_case_terms = re.findall(r'\b[A-Z][a-z]+(?:[A-Z][a-z]+)+\b', text)
                        for term in camel_case_terms:
                            # Разбиваем CamelCase на слова и добавляем в нижнем регистре
                            split_terms = re.findall(r'[A-Z][a-z]*', term)
                            if len(split_terms) >= 2:  # Только если минимум 2 слова
                                all_terms.append(' '.join(term.lower() for term in split_terms))

                    # 3. Извлекаем термины с дефисами (data-driven, real-time)
                    hyphen_terms = re.findall(r'\b[a-zA-Z]+-[a-zA-Z]+\b', text.lower())
                    all_terms.extend(hyphen_terms)

                    # 4. Извлекаем термины с подчеркиваниями (etl_pipeline, data_warehouse)
                    underscore_terms = re.findall(r'\b[a-zA-Z]+_[a-zA-Z]+\b', text.lower())
                    all_terms.extend(underscore_terms)

                # Прогресс
                if (page_num + 1) % 10 == 0 or (page_num + 1) == total_pages:
                    print(f"⏳ Обработано страниц: {page_num + 1}/{total_pages}")

    except Exception as e:
        print(f"❌ Ошибка при чтении PDF: {e}")
        print(f"   Убедитесь, что файл не поврежден и доступен для чтения")
        return None

    # Подсчитываем частоту отдельных слов
    word_counter = Counter(all_words)

    # Подсчитываем частоту терминов (многословные)
    term_counter = Counter(all_terms)

    # Фильтруем по минимальной частоте
    filtered_words = {word for word, count in word_counter.items()
                      if count >= min_frequency}

    filtered_terms = {term for term, count in term_counter.items()
                      if count >= min_frequency}

    # Собираем все термины (отдельные слова + многословные термины)
    all_filtered = sorted(list(filtered_words.union(filtered_terms)))

    # Формируем результаты
    results = {
        'all_words': all_words,
        'all_terms': all_terms,
        'word_counter': word_counter,
        'term_counter': term_counter,
        'all_filtered': all_filtered,
        'total_pages': total_pages,
        'pdf_path': pdf_path
    }

    return results


def save_statistics(results, pdf_path):
    """
    Сохраняет статистику в CSV файл с именем statistic_words_namefile.csv
    С BOM для корректного отображения кириллицы в Windows
    """
    if not results:
        return

    pdf_path = Path(pdf_path)
    stat_file = f"statistic_words_{pdf_path.stem}.csv"

    print(f"\n📊 Сохранение статистики в файл: {stat_file}")

    # Используем кодировку UTF-8 с BOM для Windows
    with open(stat_file, 'w', newline='', encoding='utf-8-sig') as csvfile:
        writer = csv.writer(csvfile)

        # Заголовки
        writer.writerow(['Метрика', 'Значение', 'Описание'])

        # Общая статистика
        writer.writerow(['Имя файла', pdf_path.name, 'Имя обработанного PDF файла'])
        writer.writerow(['Количество страниц', results['total_pages'], 'Всего страниц в книге'])
        writer.writerow(['Всего слов', len(results['all_words']), 'Слова с повторами'])
        writer.writerow(['Уникальные слова', len(results['word_counter']), 'Уникальные отдельные слова'])
        writer.writerow(['Уникальные термины', len(results['term_counter']), 'Уникальные многословные термины'])
        writer.writerow(['Отфильтрованные термины', len(results['all_filtered']), 'Все термины после фильтрации'])

        writer.writerow([])  # Пустая строка
        writer.writerow(['Топ-100 самых частых слов', '', ''])

        # Топ-100 самых частых слов
        for i, (word, count) in enumerate(results['word_counter'].most_common(100), 1):
            percentage = (count / len(results['all_words'])) * 100
            writer.writerow([f'{i}. {word}', count, f'{percentage:.2f}%'])

        writer.writerow([])  # Пустая строка
        writer.writerow(['Топ-50 самых частых терминов', '', ''])

        # Топ-50 самых частых терминов
        total_terms = sum(results['term_counter'].values())
        for i, (term, count) in enumerate(results['term_counter'].most_common(50), 1):
            if total_terms > 0:
                percentage = (count / total_terms) * 100
                writer.writerow([f'{i}. {term}', count, f'{percentage:.2f}%'])
            else:
                writer.writerow([f'{i}. {term}', count, ''])

    print(f"✅ Статистика сохранена в: {stat_file}")

    # Вывод сводной статистики в консоль
    print(f"\n{'=' * 60}")
    print(f"📊 СТАТИСТИКА ДЛЯ ФАЙЛА: {pdf_path.name}")
    print(f"{'=' * 60}")
    print(f"📝 Всего слов (с повторами): {len(results['all_words']):,}")
    print(f"🔤 Уникальных отдельных слов: {len(results['word_counter']):,}")
    print(f"🔗 Уникальных терминов (многословных): {len(results['term_counter']):,}")
    print(f"✅ Всего отфильтрованных терминов: {len(results['all_filtered']):,}")

    print(f"\n🏆 Топ-15 самых частых отдельных слов:")
    for word, count in results['word_counter'].most_common(15):
        percentage = (count / len(results['all_words'])) * 100
        print(f"  {word:<20} : {count:>4} раз ({percentage:.2f}%)")

    print(f"\n🏆 Топ-10 самых частых терминов:")
    total_terms = sum(results['term_counter'].values())
    for term, count in results['term_counter'].most_common(10):
        if total_terms > 0:
            percentage = (count / total_terms) * 100
            print(f"  {term:<30} : {count:>3} раз ({percentage:.2f}%)")
        else:
            print(f"  {term:<30} : {count:>3} раз")

    # Дополнительная статистика для консоли
    print(f"\n📈 Дополнительная статистика:")

    # Слова, которые встречаются только 1 раз
    words_once = sum(1 for count in results['word_counter'].values() if count == 1)
    print(f"  Слова, встречающиеся 1 раз: {words_once:,}")

    # Слова, которые встречаются 2-5 раз
    words_2_to_5 = sum(1 for count in results['word_counter'].values() if 2 <= count <= 5)
    print(f"  Слова, встречающиеся 2-5 раз: {words_2_to_5:,}")

    # Слова, которые встречаются более 10 раз
    words_over_10 = sum(1 for count in results['word_counter'].values() if count > 10)
    print(f"  Слова, встречающиеся >10 раз: {words_over_10:,}")


def save_all_terms(results, pdf_path):
    """
    Сохраняет все термины в CSV файл с одной колонкой 'term'
    """
    if not results:
        return

    pdf_path = Path(pdf_path)
    terms_file = f"all_terms_{pdf_path.stem}.csv"

    print(f"\n📝 Сохранение всех терминов в файл: {terms_file}")

    # Для файла с терминами используем обычный UTF-8 (без BOM)
    # так как это английские слова и они будут импортироваться в MySQL
    with open(terms_file, 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.writer(csvfile)

        # Только один заголовок
        writer.writerow(['term'])

        # Сохраняем все отфильтрованные термины
        for term in results['all_filtered']:
            writer.writerow([term])

    print(f"✅ Все термины сохранены в: {terms_file}")
    print(f"   Всего терминов: {len(results['all_filtered']):,}")

    # Сохраняем также отдельные файлы для статистики
    save_top_words_separate(results, pdf_path)
    save_top_terms_separate(results, pdf_path)


def save_top_words_separate(results, pdf_path):
    """
    Сохраняет топ-100 слов в отдельный файл для удобства
    """
    pdf_path = Path(pdf_path)
    top_words_file = f"top_100_words_{pdf_path.stem}.csv"

    with open(top_words_file, 'w', newline='', encoding='utf-8-sig') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(['Ранг', 'Слово', 'Частота', 'Процент'])

        total_words = len(results['all_words'])
        for i, (word, count) in enumerate(results['word_counter'].most_common(100), 1):
            percentage = (count / total_words) * 100
            writer.writerow([i, word, count, f"{percentage:.4f}%"])

    print(f"📊 Топ-100 слов сохранены в: {top_words_file}")


def save_top_terms_separate(results, pdf_path):
    """
    Сохраняет топ-50 терминов в отдельный файл для удобства
    """
    pdf_path = Path(pdf_path)
    top_terms_file = f"top_50_terms_{pdf_path.stem}.csv"

    with open(top_terms_file, 'w', newline='', encoding='utf-8-sig') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(['Ранг', 'Термин', 'Частота', 'Процент'])

        total_terms = sum(results['term_counter'].values())
        for i, (term, count) in enumerate(results['term_counter'].most_common(50), 1):
            if total_terms > 0:
                percentage = (count / total_terms) * 100
                writer.writerow([i, term, count, f"{percentage:.4f}%"])
            else:
                writer.writerow([i, term, count, ''])

    print(f"📊 Топ-50 терминов сохранены в: {top_terms_file}")


def show_usage(script_name):
    """Показывает справку по использованию скрипта"""
    print(f"\n{'=' * 60}")
    print(f"📖 PDF TERM EXTRACTOR - Извлечение терминов из PDF книг")
    print(f"{'=' * 60}")
    print(f"\n📄 Использование: python {script_name} <путь_к_pdf_файлу> [опции]")
    print(f"\nПримеры:")
    print(f"  python {script_name} my_book.pdf")
    print(f"  python {script_name} \"C:\\полный\\путь\\к\\файлу.pdf\"")
    print(f"\nОпции:")
    print(f"  --min-length 4       Минимальная длина слов (по умолчанию: 4)")
    print(f"  --min-freq 2         Минимальная частота слова (по умолчанию: 2)")
    print(f"  --no-camelcase       Отключить извлечение CamelCase терминов")
    print(f"\nРезультат:")
    print(f"  1. statistic_words_<имя_файла>.csv - полная статистика")
    print(f"  2. all_terms_<имя_файла>.csv - все термины для базы данных")
    print(f"  3. top_100_words_<имя_файла>.csv - топ-100 слов")
    print(f"  4. top_50_terms_<имя_файла>.csv - топ-50 терминов")
    print(f"\n{'=' * 60}")
    print(f"💡 Совет: Укажите путь к PDF файлу в переменной PDF_FILE_PATH")
    print(f"          в начале скрипта для автоматической обработки.")
    print(f"{'=' * 60}")


def main():
    """Основная функция"""
    script_name = Path(sys.argv[0]).name

    # Если нет аргументов командной строки, используем путь по умолчанию
    if len(sys.argv) < 2:
        show_usage(script_name)
        return

    # Парсим аргументы
    pdf_path = sys.argv[1]
    min_word_length = 4
    min_frequency = 2
    extract_camel_case = True

    i = 2
    while i < len(sys.argv):
        if sys.argv[i] == '--min-length':
            min_word_length = int(sys.argv[i + 1])
            i += 2
        elif sys.argv[i] == '--min-freq':
            min_frequency = int(sys.argv[i + 1])
            i += 2
        elif sys.argv[i] == '--no-camelcase':
            extract_camel_case = False
            i += 1
        else:
            print(f"⚠️  Неизвестный параметр: {sys.argv[i]}")
            print(f"   Используйте --help для просмотра доступных опций")
            show_usage(script_name)
            return

    # Извлекаем термины
    results = extract_technical_terms(
        pdf_path,
        min_word_length=min_word_length,
        min_frequency=min_frequency,
        extract_camel_case=extract_camel_case
    )

    # Сохраняем результаты
    if results:
        save_statistics(results, pdf_path)
        save_all_terms(results, pdf_path)

        print(f"\n{'=' * 60}")
        print(f"🎉 Обработка завершена успешно!")
        print(f"{'=' * 60}")
        print(f"📁 Созданные файлы для '{Path(pdf_path).name}':")
        print(f"  1. statistic_words_{Path(pdf_path).stem}.csv - полная статистика")
        print(f"  2. all_terms_{Path(pdf_path).stem}.csv - все термины для базы данных")
        print(f"  3. top_100_words_{Path(pdf_path).stem}.csv - топ-100 слов")
        print(f"  4. top_50_terms_{Path(pdf_path).stem}.csv - топ-50 терминов")
        print(f"\n💾 Файл all_terms_{Path(pdf_path).stem}.csv можно импортировать в MySQL:")
        print(f"  LOAD DATA INFILE 'all_terms_{Path(pdf_path).stem}.csv'")
        print(f"  INTO TABLE words")
        print(f"  FIELDS TERMINATED BY ','")
        print(f"  ENCLOSED BY '\"'")
        print(f"  LINES TERMINATED BY '\\n'")
        print(f"  IGNORE 1 ROWS (term);")
    else:
        print(f"\n❌ Обработка не удалась. Проверьте путь к файлу и параметры.")


if __name__ == "__main__":
    script_name = Path(sys.argv[0]).name

    print(f"\n{'=' * 60}")
    print(f"🔍 PDF TERM EXTRACTOR v1.0")
    print(f"{'=' * 60}")

    # Если нет аргументов командной строки, используем путь по умолчанию
    if len(sys.argv) == 1:
        print(f"\n📂 Проверяю наличие файла по пути по умолчанию...")
        print(f"📍 Путь: {PDF_FILE_PATH}")

        if os.path.exists(PDF_FILE_PATH):
            print(f"✅ Файл найден! Начинаю автоматическую обработку...")
            print("-" * 60)

            # Извлекаем термины с параметрами по умолчанию
            results = extract_technical_terms(
                PDF_FILE_PATH,
                min_word_length=4,
                min_frequency=2,
                extract_camel_case=True
            )

            # Сохраняем результаты
            if results:
                save_statistics(results, PDF_FILE_PATH)
                save_all_terms(results, PDF_FILE_PATH)

                print(f"\n{'=' * 60}")
                print(f"🎉 Автоматическая обработка завершена успешно!")
                print(f"{'=' * 60}")
                print(f"💡 Совет: Для обработки другого файла запустите скрипт с аргументом:")
                print(f"         python {script_name} путь_к_новому_файлу.pdf")
            else:
                print(f"\n❌ Обработка не удалась.")
                show_usage(script_name)
        else:
            print(f"❌ Файл не найден по пути: {PDF_FILE_PATH}")
            print(f"\n💡 Измените переменную PDF_FILE_PATH в начале скрипта")
            print(f"   или укажите путь к файлу при запуске:")
            print(f"   python {script_name} путь_к_вашему_файлу.pdf")
            show_usage(script_name)
    else:
        # Если есть аргументы, проверяем флаг --help
        if '--help' in sys.argv or '-h' in sys.argv:
            show_usage(script_name)
        else:
            main()