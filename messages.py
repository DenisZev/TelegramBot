from datetime import datetime

def format_date(date_str):
    try:
        date_obj = datetime.fromisoformat(date_str)
        return date_obj.strftime('%d.%m.%Y %H:%M:%S')
    except ValueError:
        return date_str  # Возвращаем оригинальный текст, если не удалось преобразовать

start_message = "Добро пожаловать в наш Телеграмм-бот! Используйте команду /check_orders для проверки новых заказов."

def orders_message(orders):
    """Формирует сообщение с новыми заказами."""
    if not orders:
        return "Нет новых заказов."

    order_list = []
    for order in orders:
        order_id = order.get('id', 'неизвестно')
        skus = order.get('skus', [])
        article = order.get('article', 'неизвестно')

        price = order.get('price', 0)
        converted_price = order.get('convertedPrice')

        sale_price = converted_price if (converted_price is not None and isinstance(converted_price, (int, float))) else price
        if sale_price is None or not isinstance(sale_price, (int, float)):
            sale_price = 0

        price_rubles = sale_price // 100
        price_kopecks = sale_price % 100
        formatted_price = f"{price_rubles},{price_kopecks:02d}" if sale_price else "Не указано"

        order_list.append(
            f"Заказ ID: {order_id}\n"
            f"SKUs: {', '.join(skus)}\n"
            f"Артикул: {article}\n"
            f"Цена: {formatted_price} руб.\n"
            f"{'-' * 30}"
        )

    return f"Вот ваши новые заказы:\n" + "\n".join(order_list)

def assembly_tasks_message(tasks):
    """Формирует сообщение с информацией по сборочным заданиям."""
    if not tasks or len(tasks) == 0:
        return "Нет сборочных заданий."

    messages = []

    for task in tasks:
        id_task = task.get('id', 'Не указано')
        article = task.get('article', 'Не указано')
        created_at = format_date(task.get('createdAt', 'Не указано'))
        price = task.get('price', 0)

        if price is None or not isinstance(price, (int, float)):
            price = 0

        price_rubles = price // 100
        price_kopecks = price % 100
        formatted_price = f"{price_rubles},{price_kopecks:02d}"

        msg = (
            f"Сборочное задание ID: {id_task}\n"
            f"Наименование: {article}\n"
            f"Создано: {created_at}\n"
            f"Цена: {formatted_price} руб.\n"
            f"--------------------------"
        )
        messages.append(msg)

    return "\n".join(messages)
