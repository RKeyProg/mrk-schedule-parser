import pdfplumber
import re

PDF_PATH = "27.01.2026.pdf"

def is_auditorium(line: str) -> bool:
    return bool(re.search(r"\d{3}", line)) or "с/з" in line or "а/з" in line

def looks_like_teacher(line: str) -> bool:
    # Фамилия + нет цифр
    return not re.search(r"\d", line) and line[0].isupper()


def find_teacher(teacher_lastname: str, pdf_path: str):
    results = []

    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            tables = page.extract_tables()

            for table in tables:
                for row in table:
                    if not row or not row[0]:
                        continue

                    group = row[0].strip()

                    if not re.match(r"\dК\d+", group):
                        continue

                    for pair_index, cell in enumerate(row[1:], start=1):
                        if not cell:
                            continue

                        lines = [l.strip() for l in cell.split("\n") if l.strip()]

                        # Ищем строку с фамилией
                        teacher_line_index = None
                        for i, line in enumerate(lines):
                            if teacher_lastname.lower() in line.lower():
                                teacher_line_index = i
                                break

                        if teacher_line_index is None:
                            continue

                        # ПРЕДМЕТ — всё, что выше фамилии
                        subject = " ".join(lines[:teacher_line_index])

                        # ПРЕПОДАВАТЕЛИ — строка с фамилией
                        teachers = [lines[teacher_line_index]]

                        # АУДИТОРИИ — строки ниже фамилии
                        auditoriums = []
                        for line in lines[teacher_line_index + 1:]:
                            if is_auditorium(line):
                                auditoriums.append(line)

                        results.append({
                            "группа": group,
                            "пара": pair_index - 1,
                            "предмет": subject,
                            "преподаватели": teachers,
                            "аудитории": auditoriums
                        })

    return results
