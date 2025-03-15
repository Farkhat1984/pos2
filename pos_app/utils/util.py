# utils.py
import re
from datetime import datetime


def validate_barcode(barcode):
    """Проверка корректности штрих-кода"""
    barcode = barcode.strip()
    if not re.match(r'^\d+$', barcode):
        return False
    valid_lengths = [8, 12, 13]
    if len(barcode) not in valid_lengths:
        return len(barcode) >= 4
    return True


def format_price(price):
    """Форматирование цены для отображения"""
    return f"{price:.2f}"


def format_date(date_str, input_format="%Y-%m-%d %H:%M:%S", output_format="%d.%m.%Y %H:%M"):
    """Форматирование даты для отображения"""
    try:
        date_obj = datetime.strptime(date_str, input_format)
        return date_obj.strftime(output_format)
    except:
        return date_str


def get_payment_status_color(status):
    """Получение цвета для статуса оплаты"""
    if status == "Оплачено":
        return (0.2, 0.7, 0.2, 1)
    elif status == "В долг":
        return (0.9, 0.4, 0.4, 1)
    else:
        return (0.9, 0.7, 0.2, 1)


def calculate_total(items):
    """Вычисление общей суммы для списка товаров"""
    return sum(item['total'] for item in items)


def generate_invoice_number():
    """Генерация номера накладной"""
    now = datetime.now()
    date_part = now.strftime("%Y%m%d")
    time_part = now.strftime("%H%M")
    return f"{date_part}-{time_part}"