import json
import os
from pathlib import Path

def check_image_extensions():
    # Путь к JSON-файлу с вопросами
    json_file_path = "questions_full.json"  # Укажите правильный путь к вашему файлу
    
    # Путь к папке с изображениями
    images_folder = "static/images/"
    
    # Получаем список всех файлов в папке с изображениями
    try:
        image_files = set(os.listdir(images_folder))
    except FileNotFoundError:
        print(f"Ошибка: Папка {images_folder} не найдена")
        return
    
    # Загружаем данные из JSON-файла
    try:
        with open(json_file_path, 'r', encoding='utf-8') as f:
            questions = json.load(f)
    except FileNotFoundError:
        print(f"Ошибка: Файл {json_file_path} не найден")
        return
    except json.JSONDecodeError:
        print(f"Ошибка: Не удалось разобрать JSON в файле {json_file_path}")
        return
    
    # Списки для хранения проблем
    missing_files = []
    wrong_extensions = []
    
    # Проверяем каждый вопрос
    for question in questions:
        # Проверяем изображение вопроса
        question_image = question.get("question_image")
        if question_image:
            base_name = Path(question_image).stem
            # Ищем файлы с тем же базовым именем
            matching_files = [f for f in image_files if Path(f).stem == base_name]
            
            if not matching_files:
                missing_files.append(question_image)
            elif question_image not in image_files:
                actual_file = matching_files[0]
                wrong_extensions.append((question_image, actual_file))
        
        # Проверяем изображение ответа
        answer_image = question.get("answer_image")
        if answer_image:
            base_name = Path(answer_image).stem
            # Ищем файлы с тем же базовым именем
            matching_files = [f for f in image_files if Path(f).stem == base_name]
            
            if not matching_files:
                missing_files.append(answer_image)
            elif answer_image not in image_files:
                actual_file = matching_files[0]
                wrong_extensions.append((answer_image, actual_file))
    
    # Выводим результаты
    if missing_files:
        print("Отсутствующие файлы:")
        for file in missing_files:
            print(f"  - {file}")
        print()
    
    if wrong_extensions:
        print("Неправильные расширения:")
        for expected, actual in wrong_extensions:
            expected_ext = Path(expected).suffix
            actual_ext = Path(actual).suffix
            print(f"  - {expected} (ожидается {expected_ext}) -> {actual} (фактически {actual_ext})")
        print()
    
    if not missing_files and not wrong_extensions:
        print("Все файлы изображений найдены и имеют правильные расширения.")
    else:
        total_issues = len(missing_files) + len(wrong_extensions)
        print(f"Всего проблем: {total_issues}")

if __name__ == "__main__":
    check_image_extensions()