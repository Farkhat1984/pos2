import re
from datetime import datetime


def validate_barcode(barcode):
    """
    Проверяет, является ли строка корректным штрих-кодом.

    Args:
        barcode (str): Строка для проверки.

    Returns:
        bool: True, если штрих-код корректен, False в противном случае.
    """
    barcode = barcode.strip()
    if not re.match(r'^\d+$', barcode):
        return False
    valid_lengths = [8, 12, 13]
    if len(barcode) not in valid_lengths:
        return len(barcode) >= 4 # Разрешаем произвольные штрих-коды >= 4 символов
    return True


def format_price(price):
    """
    Форматирует цену для отображения в пользовательском интерфейсе.

    Args:
        price (float): Цена для форматирования.

    Returns:
        str: Строка с отформатированной ценой (два знака после запятой).
    """
    return f"{price:.2f}"


def format_date(date_str, input_format="%Y-%m-%d %H:%M:%S", output_format="%d.%m.%Y %H:%M"):
    """
    Форматирует дату из строки в заданный формат.

    Args:
        date_str (str): Строка с датой.
        input_format (str): Формат входной строки даты.
        output_format (str): Желаемый формат выходной строки даты.

    Returns:
        str: Отформатированная строка даты.
    """
    try:
        date_obj = datetime.strptime(date_str, input_format)
        return date_obj.strftime(output_format)
    except:
        return date_str # Возвращаем исходную строку в случае ошибки


def get_payment_status_color(status):
    """
    Возвращает цвет в формате RGBA для статуса оплаты.

    Args:
        status (str): Статус оплаты ("Оплачено", "В долг" и т.д.).

    Returns:
        tuple: Кортеж RGBA цвета.
    """
    if status == "Оплачено":
        return (0.2, 0.7, 0.2, 1)  # Зеленый
    elif status == "В долг":
        return (0.9, 0.4, 0.4, 1)  # Красный
    else:
        return (0.9, 0.7, 0.2, 1)  # Желтый (для частичной оплаты)


def calculate_total(items):
    """
    Вычисляет общую сумму для списка товаров.

    Args:
        items (list): Список товаров, каждый элемент которого должен иметь ключ 'total'.

    Returns:
        float: Общая сумма стоимостей товаров.
    """
    return sum(item['total'] for item in items)


def generate_invoice_number():
    """
    Генерирует номер накладной на основе текущей даты и времени.
    В реальном приложении может потребоваться более сложная логика.

    Returns:
        str: Сгенерированный номер накладной в формате YYYYMMDD-HHMM.
    """
    now = datetime.now()
    date_part = now.strftime("%Y%m%d")
    time_part = now.strftime("%H%M")
    return f"{date_part}-{time_part}"