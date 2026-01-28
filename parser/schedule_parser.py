import pdfplumber
import re


def is_auditorium(line: str) -> bool:
    """Проверяет, является ли строка аудиторией"""
    return bool(re.search(r"\d{3}", line)) or "с/з" in line or "а/з" in line


def parse_header_row(row):
    """
    Парсит заголовок таблицы и создает маппинг столбцов на номера пар.
    
    Args:
        row: Строка заголовка таблицы
        
    Returns:
        Словарь {индекс_столбца: номер_пары}
    """
    pair_mapping = {}
    for i, cell in enumerate(row):
        if cell and re.search(r"(\d+)\s*пара", cell):
            match = re.search(r"(\d+)\s*пара", cell)
            pair_number = int(match.group(1))
            pair_mapping[i] = pair_number
    return pair_mapping


def find_teacher(teacher_lastname: str, pdf_path: str):
    """
    Ищет расписание преподавателя в PDF файле.
    
    Args:
        teacher_lastname: Фамилия преподавателя (может быть с инициалами)
        pdf_path: Путь к PDF файлу с расписанием
        
    Returns:
        Список словарей с информацией о занятиях
    """
    results = []

    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            tables = page.extract_tables()

            for table in tables:
                if not table or len(table) < 2:
                    continue
                
                # Ищем строку заголовка (содержит "пара")
                pair_mapping = None
                header_row_index = 0
                
                for i, row in enumerate(table):
                    if row and any(cell and "пара" in cell for cell in row):
                        pair_mapping = parse_header_row(row)
                        header_row_index = i
                        break
                
                # Если не нашли заголовок, используем простую индексацию
                if not pair_mapping:
                    pair_mapping = {i: i for i in range(1, 8)}
                    
                # Парсим строки с данными (после заголовка)
                for row in table[header_row_index + 1:]:
                    if not row or not row[0]:
                        continue

                    group = row[0].strip()

                    # Проверка формата группы (например, 3К9091)
                    if not re.match(r"\dК\d+", group):
                        continue

                    # Проходим по всем столбцам (кроме первого с группой)
                    for col_index in range(1, len(row)):
                        cell = row[col_index]
                        
                        if not cell:
                            continue

                        lines = [l.strip() for l in cell.split("\n") if l.strip()]
                        
                        if not lines:
                            continue

                        # Ищем строку с преподавателем
                        teacher_line_index = None
                        for i, line in enumerate(lines):
                            # Поиск по фамилии (с учетом инициалов)
                            if teacher_lastname.lower() in line.lower():
                                # Проверка, что это строка с преподавателем
                                # (нет цифр, кроме точек в инициалах)
                                line_without_dots = line.replace(".", "")
                                if not re.search(r"\d", line_without_dots):
                                    teacher_line_index = i
                                    break

                        if teacher_line_index is None:
                            continue

                        # ПРЕДМЕТ — всё, что выше строки с преподавателем
                        subject_lines = lines[:teacher_line_index]
                        subject = " ".join(subject_lines) if subject_lines else "Не указан"

                        # ПРЕПОДАВАТЕЛИ — полная строка с фамилией
                        teachers_line = lines[teacher_line_index]

                        # АУДИТОРИИ — строки ниже, содержащие номера аудиторий
                        auditoriums = []
                        for line in lines[teacher_line_index + 1:]:
                            if is_auditorium(line):
                                auditoriums.append(line)

                        # Определяем номер пары по маппингу
                        pair_number = pair_mapping.get(col_index, col_index)

                        results.append({
                            "группа": group,
                            "пара": pair_number,
                            "предмет": subject,
                            "преподаватели": teachers_line,
                            "аудитории": ", ".join(auditoriums) if auditoriums else "Не указана"
                        })

    # Сортируем результаты по номеру пары
    results.sort(key=lambda x: x["пара"])
    
    return results
